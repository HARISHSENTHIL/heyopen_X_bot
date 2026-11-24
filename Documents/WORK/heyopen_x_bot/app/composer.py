REPLY_CHAR_LIMIT = 280


def compose_reply(author_username: str, body: str) -> str:
    # X replies via the API thread correctly only when the text itself leads with
    # the @mention of who you're replying to — the API doesn't inject it for you.
    prefix = f"@{author_username} "
    budget = REPLY_CHAR_LIMIT - len(prefix)
    if len(body) > budget:
        body = body[: budget - 1].rstrip() + "…"
    return prefix + body
