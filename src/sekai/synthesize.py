from __future__ import annotations

import json

from sekai.contracts import RawItem, Synthesis, View

MODEL_NAME = "claude-3-5-haiku-latest"
MAX_TOKENS = 4096


class SynthesizeError(RuntimeError):
    """Raised when the LLM response can't be parsed into a Synthesis."""


def _build_prompt(topic: str, items: list[RawItem]) -> str:
    sources = "\n\n".join(
        f"[{i}] link={item.link}\n{item.text}"
        for i, item in enumerate(items, start=1)
    )
    return f"""You are synthesizing English-language online discourse about \
"{topic}" for a Japanese reader. Use ONLY the numbered sources below — \
do not invent claims, views, or sources that aren't grounded in them. Every \
view in your output must cite the exact "link" value of one of the sources \
below.

Sources:
{sources}

Respond with ONLY a single JSON object (no markdown fences, no commentary, \
no leading or trailing text) matching exactly this shape:

{{
  "topic": "{topic}",
  "generated_at": "<ISO-8601 timestamp>",
  "consensus_ja": "<the broad agreement, in Japanese>",
  "tensions_ja": "<where opinion splits, in Japanese>",
  "views": [
    {{
      "stance": "<short label>",
      "summary_ja": "<translated, culturally-framed summary, in Japanese>",
      "source": "reddit",
      "link": "<must exactly match one of the source links above>",
      "why_surprising": "<optional note for the JP reader, or null>"
    }}
  ]
}}
"""


def synthesize(topic: str, items: list[RawItem], llm_client) -> Synthesis:
    """Call the LLM once and parse its response into a Synthesis.

    `llm_client` is expected to be anthropic.Anthropic-shaped (or a test fake
    with the same `messages.create(...) -> response.content[0].text` shape).
    No retry/grounding-validation loop yet — see .ralph/specs/issue-1.md.
    """
    prompt = _build_prompt(topic, items)

    response = llm_client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = response.content[0].text

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise SynthesizeError(f"LLM returned invalid JSON: {exc}") from exc

    try:
        views = [
            View(
                stance=v["stance"],
                summary_ja=v["summary_ja"],
                source=v["source"],
                link=v["link"],
                why_surprising=v.get("why_surprising"),
            )
            for v in payload["views"]
        ]
        return Synthesis(
            topic=payload["topic"],
            generated_at=payload["generated_at"],
            consensus_ja=payload["consensus_ja"],
            tensions_ja=payload["tensions_ja"],
            views=views,
        )
    except (KeyError, TypeError) as exc:
        raise SynthesizeError(f"LLM JSON missing required field: {exc}") from exc
