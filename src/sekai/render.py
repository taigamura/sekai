from __future__ import annotations

from sekai.contracts import Synthesis


def render(synthesis: Synthesis) -> str:
    """Pure function: Synthesis JSON -> Markdown report string."""
    lines = [
        f"# {synthesis.topic}",
        "",
        f"_Generated {synthesis.generated_at}_",
        "",
        "## Consensus",
        "",
        synthesis.consensus_ja,
        "",
        "## Tensions",
        "",
        synthesis.tensions_ja,
        "",
        "## Views",
        "",
    ]

    for view in synthesis.views:
        lines.append(f"### {view.stance}")
        lines.append("")
        lines.append(view.summary_ja)
        lines.append("")
        if view.why_surprising:
            lines.append(f"> {view.why_surprising}")
            lines.append("")
        lines.append(f"Source: [{view.source}]({view.link})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
