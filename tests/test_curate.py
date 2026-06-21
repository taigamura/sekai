from sekai.contracts import RawItem
from sekai.curate import curate


def make_item(id, text, score):
    return RawItem(
        id=id,
        source="reddit",
        author="someone",
        text=text,
        link=f"https://reddit.com/comments/{id}/",
        score=score,
        created_at="2026-06-01T00:00:00+00:00",
    )


def test_drops_too_short_text():
    items = [make_item("a", "too short", 100), make_item("b", "a" * 30, 1)]

    result = curate(items, max_items=15)

    assert [item.id for item in result] == ["b"]


def test_ranks_by_score_descending():
    items = [
        make_item("low", "x" * 30, score=1),
        make_item("high", "x" * 30, score=100),
        make_item("mid", "x" * 30, score=50),
    ]

    result = curate(items, max_items=15)

    assert [item.id for item in result] == ["high", "mid", "low"]


def test_keeps_only_top_max_items():
    items = [make_item(str(i), "x" * 30, score=i) for i in range(20)]

    result = curate(items, max_items=5)

    assert len(result) == 5
    assert [item.id for item in result] == ["19", "18", "17", "16", "15"]
