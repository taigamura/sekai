import datetime as dt
import json

import pytest

from sekai.container import container


class FakeAuthor:
    def __init__(self, name: str):
        self._name = name

    def __str__(self) -> str:
        return self._name


class FakeSubmission:
    def __init__(
        self,
        id: str,
        title: str,
        selftext: str,
        score: int,
        created_utc: float,
        permalink: str,
        author: str = "someone",
    ):
        self.id = id
        self.title = title
        self.selftext = selftext
        self.score = score
        self.created_utc = created_utc
        self.permalink = permalink
        self.author = FakeAuthor(author) if author else None


class FakeSubreddit:
    def __init__(self, submissions):
        self._submissions = submissions

    def search(self, query, time_filter=None, sort=None):
        return iter(self._submissions)


class FakeRedditClient:
    """praw.Reddit-shaped fake for exercising fetch_reddit without network."""

    def __init__(self, submissions):
        self._subreddit = FakeSubreddit(submissions)

    def subreddit(self, name):
        return self._subreddit


class FakeMessageContentBlock:
    def __init__(self, text: str):
        self.text = text


class FakeMessageResponse:
    def __init__(self, text: str):
        self.content = [FakeMessageContentBlock(text)]


class FakeMessages:
    def __init__(self, response_texts):
        self._response_texts = list(response_texts)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = self._response_texts[min(len(self.calls) - 1, len(self._response_texts) - 1)]
        return FakeMessageResponse(text)


class FakeAnthropicClient:
    """anthropic.Anthropic-shaped fake for exercising synthesize without network."""

    def __init__(self, response_text_or_texts):
        if isinstance(response_text_or_texts, str):
            response_texts = [response_text_or_texts]
        else:
            response_texts = response_text_or_texts
        self.messages = FakeMessages(response_texts)

    @property
    def call_count(self) -> int:
        return len(self.messages.calls)


def make_submission(id, title, selftext, score, link_suffix, age_days=1, author="someone"):
    created_utc = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=age_days)).timestamp()
    return FakeSubmission(
        id=id,
        title=title,
        selftext=selftext,
        score=score,
        created_utc=created_utc,
        permalink=f"/r/all/comments/{id}/{link_suffix}/",
        author=author,
    )


def reddit_link(id: str, link_suffix: str) -> str:
    return f"https://reddit.com/r/all/comments/{id}/{link_suffix}/"


def make_synthesis_payload(topic: str, views: list[dict]) -> str:
    return json.dumps(
        {
            "topic": topic,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "consensus_ja": "概ね好意的に受け止められている。",
            "tensions_ja": "観光客の増加を歓迎する声と、混雑を嫌がる声がある。",
            "views": views,
        }
    )


@pytest.fixture
def reddit_credentials(monkeypatch):
    monkeypatch.setenv("REDDIT_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("REDDIT_USER_AGENT", "test-user-agent")


@pytest.fixture
def anthropic_credentials(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")


@pytest.fixture
def all_credentials(reddit_credentials, anthropic_credentials):
    pass


@pytest.fixture
def override_reddit_client():
    def _override(fake_client):
        container.reddit_client.override(fake_client)

    yield _override
    container.reddit_client.reset_override()


@pytest.fixture
def override_anthropic_client():
    def _override(fake_client):
        container.anthropic_client.override(fake_client)

    yield _override
    container.anthropic_client.reset_override()
