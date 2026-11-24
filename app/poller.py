import logging
import threading
import time

from app.composer import compose_reply
from app.config import settings
from app.db import Store
from app.geo import is_us_location
from app.llm import explain_post
from app.x_client import XClient

log = logging.getLogger("poller")


class Poller:
    def __init__(self):
        self.store = Store(settings.db_path)
        self.x = XClient()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.status_lock = threading.Lock()
        self.status = {
            "last_poll_at": None,
            "last_error": None,
            "replies_today": 0,
            "skipped_unverified": 0,
            "skipped_non_us": 0,
        }

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self):
        while not self._stop.is_set():
            try:
                self.process_once()
                with self.status_lock:
                    self.status["last_error"] = None
            except Exception as exc:  # noqa: BLE001 — poller must survive one bad cycle
                log.exception("poll cycle failed")
                with self.status_lock:
                    self.status["last_error"] = str(exc)
            with self.status_lock:
                self.status["last_poll_at"] = time.time()
                self.status["replies_today"] = self.store.replies_today()
            self._stop.wait(settings.poll_interval_seconds)

    def process_once(self):
        since_id = self.store.get_since_id()
        mentions = self.x.fetch_mentions(since_id)

        for mention in mentions:
            # Always advance since_id, even on skip, so a bad mention can't wedge the poller.
            self.store.set_since_id(mention.tweet_id)

            if self.store.already_processed(mention.tweet_id):
                continue

            if settings.require_verified_author and mention.author_verified_type == "none":
                log.info("skipping unverified author %s", mention.author_username)
                with self.status_lock:
                    self.status["skipped_unverified"] += 1
                self.store.mark_processed(mention.tweet_id, mention.author_id, replied=False)
                continue

            if settings.require_us_author and not is_us_location(mention.author_location):
                log.info(
                    "skipping non-US author %s (location=%r)",
                    mention.author_username,
                    mention.author_location,
                )
                with self.status_lock:
                    self.status["skipped_non_us"] += 1
                self.store.mark_processed(mention.tweet_id, mention.author_id, replied=False)
                continue

            if self.store.replies_today() >= settings.max_replies_per_day:
                log.warning("daily reply budget hit, skipping %s", mention.tweet_id)
                self.store.mark_processed(mention.tweet_id, mention.author_id, replied=False)
                continue

            if (
                self.store.replies_today_for_author(mention.author_id)
                >= settings.max_replies_per_author_per_day
            ):
                log.info("per-author budget hit for %s", mention.author_id)
                self.store.mark_processed(mention.tweet_id, mention.author_id, replied=False)
                continue

            try:
                body = explain_post(
                    mention.text, mention.parent_text, mention.parent_author_username
                )
                reply_text = compose_reply(mention.author_username, body)
                self.x.reply(mention.tweet_id, reply_text)
                self.store.mark_processed(mention.tweet_id, mention.author_id, replied=True)
            except Exception:
                log.exception("failed to answer mention %s", mention.tweet_id)
                self.store.mark_processed(mention.tweet_id, mention.author_id, replied=False)
