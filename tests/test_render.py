from sekai.contracts import Synthesis, View
from sekai.render import render


def test_renders_topic_consensus_tensions_and_views():
    synthesis = Synthesis(
        topic="ramen tourism",
        generated_at="2026-06-22T00:00:00+00:00",
        consensus_ja="概ね好意的に受け止められている。",
        tensions_ja="混雑を歓迎する声と嫌がる声がある。",
        views=[
            View(
                stance="Pro-tourism",
                summary_ja="観光客の増加は店の収益に良い影響を与えている。",
                source="reddit",
                link="https://reddit.com/comments/abc123/",
                why_surprising=None,
            ),
            View(
                stance="Local backlash",
                summary_ja="常連客は行列の長さに不満を持っている。",
                source="reddit",
                link="https://reddit.com/comments/def456/",
                why_surprising="観光公害への懸念は日本国内の議論にも通じる。",
            ),
        ],
    )

    report = render(synthesis)

    assert report.startswith("# ramen tourism")
    assert "概ね好意的に受け止められている。" in report
    assert "混雑を歓迎する声と嫌がる声がある。" in report
    assert "### Pro-tourism" in report
    assert "https://reddit.com/comments/abc123/" in report
    assert "### Local backlash" in report
    assert "観光公害への懸念は日本国内の議論にも通じる。" in report
    assert "https://reddit.com/comments/def456/" in report


def test_omits_why_surprising_block_when_absent():
    synthesis = Synthesis(
        topic="t",
        generated_at="2026-06-22T00:00:00+00:00",
        consensus_ja="c",
        tensions_ja="t",
        views=[
            View(
                stance="Stance",
                summary_ja="summary",
                source="reddit",
                link="https://reddit.com/comments/x/",
                why_surprising=None,
            ),
        ],
    )

    report = render(synthesis)

    assert ">" not in report
