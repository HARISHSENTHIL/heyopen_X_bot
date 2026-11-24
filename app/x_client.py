from dataclasses import dataclass

import tweepy

from app.config import settings


@dataclass
class MentionContext:
    tweet_id: str
    text: str
    author_id: str
    author_username: str
    # "none" | "blue" | "business" | "government" — "none" means not X-verified.
    author_verified_type: str
    # Free-text profile location. X has no account-country field; this is all we get.
    author_location: str | None
    # Text of the post being replied-to/quoted, if any — the thing the user is actually asking about.
    parent_text: str | None
    parent_author_username: str | None


class XClient:
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=settings.x_bearer_token,
            consumer_key=settings.x_consumer_key,
            consumer_secret=settings.x_consumer_secret,
            access_token=settings.x_access_token,
            access_token_secret=settings.x_access_token_secret,
            wait_on_rate_limit=True,
        )
        self._bot_user_id: str | None = None

    @property
    def bot_user_id(self) -> str:
        if self._bot_user_id is None:
            me = self.client.get_me()
            self._bot_user_id = me.data.id
        return self._bot_user_id

    def fetch_mentions(self, since_id: str | None) -> list[MentionContext]:
        resp = self.client.get_users_mentions(
            id=self.bot_user_id,
            since_id=since_id,
            max_results=50,
            expansions=[
                "referenced_tweets.id",
                "referenced_tweets.id.author_id",
                "author_id",
            ],
            tweet_fields=["created_at", "text", "referenced_tweets", "author_id"],
            user_fields=["username", "verified_type", "location"],
        )
        if not resp.data:
            return []

        users_by_id = {u.id: u for u in (resp.includes.get("users") or [])}
        tweets_by_id = {t.id: t for t in (resp.includes.get("tweets") or [])}

        out = []
        # API returns newest-first; process oldest-first so since_id advances correctly.
        for tweet in reversed(resp.data):
            author = users_by_id.get(tweet.author_id)
            parent_text = None
            parent_author_username = None
            for ref in tweet.referenced_tweets or []:
                if ref.type in ("replied_to", "quoted"):
                    parent = tweets_by_id.get(ref.id)
                    if parent:
                        parent_text = parent.text
                        parent_author = users_by_id.get(parent.author_id)
                        parent_author_username = (
                            parent_author.username if parent_author else None
                        )
                    break
            out.append(
                MentionContext(
                    tweet_id=tweet.id,
                    text=tweet.text,
                    author_id=tweet.author_id,
                    author_username=author.username if author else "there",
                    author_verified_type=author.verified_type if author else "none",
                    author_location=getattr(author, "location", None) if author else None,
                    parent_text=parent_text,
                    parent_author_username=parent_author_username,
                )
            )
        return out

    def reply(self, tweet_id: str, text: str) -> None:
        self.client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
