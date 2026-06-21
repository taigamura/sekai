# Sekai (世界) — MVP Specification

*Working title — rename freely.*
*Last updated: 2026-06-21*

---

## 1. Summary

A local command-line tool that, given a **topic**, fetches related discourse from free online sources, synthesizes the range of opinion, and outputs a **translated, culturally-framed summary** (English-language discourse → Japanese reader) as a Markdown report. Runs entirely locally at ~$0.

The MVP is the reusable **engine** only: four independent stages (Fetch → Curate → Synthesize → Render) connected by a defined data contract. No cloud, no video, no UI.

---

## 2. Scope

**In scope**
- One direction: EN→JP.
- Free sources only (start with 1–2).
- The four-stage pipeline as independent modules.
- A single renderer: Markdown / text report.
- A runnable CLI.

**Out of scope**
- Cloud deployment, web UI, mobile.
- Video, audio, or tweet rendering.
- Paid sources (X/Twitter), real-time/streaming ingestion.
- Multi-language beyond EN→JP.

---

## 3. Architecture

```
topic ──▶ [1] Fetch ──▶ [2] Curate ──▶ [3] Synthesize ──▶ [4] Render ──▶ report.md
            (raw items)   (shortlist)     (synthesis JSON)    (markdown)
```

Each stage is an **independent module** with an explicit input and output. Stages communicate only through the data contracts below — this keeps the renderer swappable and the pipeline portable later.

---

## 4. Data Contracts

**RawItem** (output of Fetch, input to Curate):

```json
{
  "id": "source-unique-id",
  "source": "reddit | bluesky | hn | news",
  "author": "string",
  "text": "string",
  "link": "url",
  "score": 0,
  "created_at": "ISO-8601",
  "lang": "en"
}
```

**Synthesis** (output of Synthesize, input to Render):

```json
{
  "topic": "string",
  "generated_at": "ISO-8601",
  "consensus_ja": "the broad agreement, if any",
  "tensions_ja": "where opinion splits",
  "views": [
    {
      "stance": "short label",
      "summary_ja": "translated, culturally-framed summary",
      "source": "reddit | bluesky | hn | news",
      "link": "url",
      "why_surprising": "optional note for the JP reader"
    }
  ]
}
```

---

## 5. Stage Specifications

### 5.1 Fetch
- **Input:** `topic` (string); config (enabled sources, `max_items` per source, recency window).
- **Behavior:** query each enabled source's search API for the topic; normalize results into `RawItem`; dedup by `id`/`link`; handle empty results and rate limits gracefully.
- **Output:** `List[RawItem]`.
- **Suggested libs:** PRAW (Reddit), `atproto` or httpx (Bluesky), requests (Hacker News Algolia API), feedparser (news RSS).

### 5.2 Curate
- **Input:** `List[RawItem]`.
- **Behavior:** remove near-duplicates and noise (too short, deleted/removed, off-topic); rank by a simple relevance + engagement heuristic; keep the top **N** (default 10–20).
- **Output:** ranked, trimmed `List[RawItem]` (the shortlist).
- **Note:** heuristic ranking is sufficient for MVP; an optional lightweight LLM relevance pass can be added later.

### 5.3 Synthesize
- **Input:** `topic` + shortlist (`List[RawItem]`).
- **Behavior:** one LLM call that (a) identifies the spectrum of views — consensus, surprising takes, tensions; (b) translates and culturally frames each for a Japanese reader; (c) returns JSON matching the **Synthesis** contract. Must be grounded strictly in the provided items (every view keeps its source `link`); no invented content.
- **Output:** `Synthesis` JSON.
- **Model:** local Qwen via Ollama (free) **or** Claude Haiku via API (cheap, higher quality).
- **Note:** force JSON-only output; on parse failure, retry/repair; flag low-confidence results.

### 5.4 Render
- **Input:** `Synthesis` JSON.
- **Behavior:** produce a Markdown report — topic heading, consensus, tensions, then each view with its stance, Japanese summary, "why surprising" note, and source link.
- **Output:** `report.md` (and/or stdout).
- **Note:** this is the swappable layer; the MVP ships the Markdown renderer only.

---

## 6. CLI Interface

```bash
python sekai.py --topic "ramen tourism in Japan" \
                --sources reddit,bluesky \
                --model haiku \
                --max-items 15 \
                --out report.md
```

| Flag | Default | Description |
|------|---------|-------------|
| `--topic` | (required) | The subject to research. |
| `--sources` | `reddit,bluesky` | Comma-separated enabled sources. |
| `--model` | `qwen` | `qwen` (local) or `haiku` (API). |
| `--max-items` | `15` | Items to keep after curation. |
| `--out` | `report.md` | Output file path. |

---

## 7. Tech Stack (local)

| Concern | Tool |
|---------|------|
| Language | Python 3.11+ |
| HTTP / sources | httpx / requests, PRAW, atproto, feedparser |
| State / dedup cache | SQLite or JSON (optional for MVP) |
| LLM | Ollama (Qwen) or Anthropic SDK (Claude Haiku) |
| Output | Markdown |

---

## 8. Data Sources (MVP)

| Source | Access | Auth | Notes |
|--------|--------|------|-------|
| Reddit | Official API (PRAW) | OAuth (free tier) | Non-commercial use; good coverage. |
| Bluesky | AT Protocol public API | App password / open reads | Open firehose; primary recommended source. |
| Hacker News | Algolia HN Search API | None | Optional; tech-leaning. |
| News | RSS feeds | None | Optional; broad topical coverage. |

---

## 9. Constraints

- **Free sources only**; no paid APIs in the MVP.
- **Respect each source's API terms** and rate limits.
- **Ground all output in sources** — every view retains a working link; the LLM must not invent content.
- **Cost ≈ $0** (or pennies if using the Haiku API).
- Stages must remain **independent and contract-conformant** (no cross-stage coupling).

---

## 10. Deliverables

- A runnable CLI implementing all four stages.
- The two data contracts (RawItem, Synthesis) defined in code.
- At least the Reddit and Bluesky fetch adapters.
- The Markdown renderer.
- A short README with setup and run instructions.

---

## 11. Acceptance Criteria

- For 3–5 test topics, the tool produces a coherent Japanese Markdown report capturing the consensus and at least one surprising take, with valid source links.
- The pipeline runs end-to-end locally; total cost ≈ $0 (or trivial with Haiku).
- Each stage is an independent module conforming to its contract.
- Empty or failed source responses are handled without crashing.

---

## 12. Open Decisions (to confirm before build)

- First sources to wire up (suggested: Reddit + Bluesky).
- LLM for synthesis: local Qwen vs Claude Haiku.
- Curation ranking heuristic (score-based vs LLM-assisted).
- Default `max-items` and recency window.
