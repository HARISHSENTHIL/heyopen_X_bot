import sqlite3
import threading
from contextlib import contextmanager
from datetime import date
from pathlib import Path


class Store:
    """Sqlite-backed dedupe log + daily reply budget. One writer thread (the poller),
    so a single connection with a lock is enough — no pool needed at this volume."""

    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS processed_mentions (
                tweet_id TEXT PRIMARY KEY,
                author_id TEXT NOT NULL,
                day TEXT NOT NULL,
                replied INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )"""
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._conn.commit()

    @contextmanager
    def _cursor(self):
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            finally:
                cur.close()

    def get_since_id(self) -> str | None:
        with self._cursor() as cur:
            row = cur.execute(
                "SELECT value FROM state WHERE key = 'since_id'"
            ).fetchone()
            return row[0] if row else None

    def set_since_id(self, tweet_id: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO state (key, value) VALUES ('since_id', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (tweet_id,),
            )

    def already_processed(self, tweet_id: str) -> bool:
        with self._cursor() as cur:
            row = cur.execute(
                "SELECT 1 FROM processed_mentions WHERE tweet_id = ?", (tweet_id,)
            ).fetchone()
            return row is not None

    def replies_today(self) -> int:
        today = date.today().isoformat()
        with self._cursor() as cur:
            row = cur.execute(
                "SELECT COUNT(*) FROM processed_mentions WHERE day = ? AND replied = 1",
                (today,),
            ).fetchone()
            return row[0]

    def replies_today_for_author(self, author_id: str) -> int:
        today = date.today().isoformat()
        with self._cursor() as cur:
            row = cur.execute(
                "SELECT COUNT(*) FROM processed_mentions "
                "WHERE day = ? AND author_id = ? AND replied = 1",
                (today, author_id),
            ).fetchone()
            return row[0]

    def mark_processed(self, tweet_id: str, author_id: str, replied: bool) -> None:
        today = date.today().isoformat()
        with self._cursor() as cur:
            cur.execute(
                "INSERT OR IGNORE INTO processed_mentions "
                "(tweet_id, author_id, day, replied) VALUES (?, ?, ?, ?)",
                (tweet_id, author_id, today, int(replied)),
            )
