from __future__ import annotations

from sekai.contracts import RawItem

# A fuller noise filter and recency-weighted ranking heuristic lands in a
# later slice (see .ralph/specs/issue-1.md); this is the minimal version.
MIN_TEXT_LENGTH = 20


def curate(items: list[RawItem], max_items: int) -> list[RawItem]:
    """Drop empty/too-short items and keep the top `max_items` by raw score."""
    filtered = [item for item in items if len(item.text.strip()) >= MIN_TEXT_LENGTH]
    ranked = sorted(filtered, key=lambda item: item.score, reverse=True)
    return ranked[:max_items]
