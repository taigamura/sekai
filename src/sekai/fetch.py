from __future__ import annotations

import datetime as dt

from sekai.contracts import RawItem

# Slice 1 (this module) intentionally fetches submissions only; top-level
# comments are added in a later slice (see .ralph/specs/issue-1.md).
RECENCY_WINDOW_DAYS = 30
SEARCH_TIME_FILTER = "month"  # praw's closest built-in bucket to a 30-day window


def fetch_reddit(topic: str, reddit_client) -> list[RawItem]:
    """Search r/all for `topic` and return matching submissions as RawItems.

    `reddit_client` is expected to be praw.Reddit-shaped (or a test fake with
    the same `subreddit(name).search(query, time_filter=..., sort=...)` shape).
    """
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=RECENCY_WINDOW_DAYS)
    seen_ids: set[str] = set()
    items: list[RawItem] = []

    submissions = reddit_client.subreddit("all").search(
        topic, time_filter=SEARCH_TIME_FILTER, sort="relevance"
    )

    for submission in submissions:
        if submission.id in seen_ids:
            continue

        created_at = dt.datetime.fromtimestamp(
            submission.created_utc, tz=dt.timezone.utc
        )
        if created_at < cutoff:
            continue

        seen_ids.add(submission.id)

        text = submission.title
        if getattr(submission, "selftext", ""):
            text = f"{text}\n\n{submission.selftext}"

        author = str(submission.author) if submission.author else "[deleted]"
        link = f"https://reddit.com{submission.permalink}"

        items.append(
            RawItem(
                id=submission.id,
                source="reddit",
                author=author,
                text=text,
                link=link,
                score=submission.score,
                created_at=created_at.isoformat(),
                lang="en",
            )
        )

    return items
