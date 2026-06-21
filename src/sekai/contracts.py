from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

Source = Literal["reddit", "bluesky", "hn", "news"]


@dataclass(frozen=True)
class RawItem:
    id: str
    source: Source
    author: str
    text: str
    link: str
    score: int
    created_at: str
    lang: str = "en"


@dataclass(frozen=True)
class View:
    stance: str
    summary_ja: str
    source: Source
    link: str
    why_surprising: Optional[str] = None


@dataclass(frozen=True)
class Synthesis:
    topic: str
    generated_at: str
    consensus_ja: str
    tensions_ja: str
    views: list[View] = field(default_factory=list)
