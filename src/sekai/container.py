from __future__ import annotations

import os

import anthropic
import praw
from dependency_injector import containers, providers


class MissingCredentialsError(RuntimeError):
    """Raised when required API credentials are missing from the environment."""


def _build_reddit_client() -> praw.Reddit:
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT")

    missing = [
        name
        for name, value in (
            ("REDDIT_CLIENT_ID", client_id),
            ("REDDIT_CLIENT_SECRET", client_secret),
            ("REDDIT_USER_AGENT", user_agent),
        )
        if not value
    ]
    if missing:
        raise MissingCredentialsError(
            "Missing Reddit credentials: " + ", ".join(missing)
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def _build_anthropic_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise MissingCredentialsError(
            "Missing Anthropic credentials: ANTHROPIC_API_KEY"
        )
    return anthropic.Anthropic(api_key=api_key)


class Container(containers.DeclarativeContainer):
    """Wires concrete API clients. Resolved only at the CLI entrypoint;
    every pipeline stage receives its client as an explicit parameter."""

    reddit_client = providers.Singleton(_build_reddit_client)
    anthropic_client = providers.Singleton(_build_anthropic_client)


container = Container()
