# Sekai: skeleton end-to-end pipeline (topic to Japanese Markdown report)

> GitHub issue #2 | Labels: ready-for-agent | https://github.com/taigamura/sekai/issues/2

## Parent

#1

## What to build

The end-to-end tracer bullet for the Sekai pipeline: a runnable CLI that takes a topic, fetches real Reddit submissions, curates them with a basic filter, synthesizes a Japanese-language report via Claude Haiku, and renders it to Markdown. This slice establishes the project's full architecture — package layout, dependency injection, data contracts, and CLI surface — that every later slice deepens without restructuring.

End-to-end behavior: running `sekai --topic "<topic>"` against real Reddit and Anthropic APIs produces a real `report.md` with a consensus, tensions, and at least one view with a working source link, all translated and culturally framed for a Japanese reader. Later slices will deepen Fetch (add comments), Curate (real ranking heuristic), and Synthesize (retry/grounding loop) — this slice's versions of those stages are intentionally minimal but real, not stubs.

Specifics:
- **Project setup:** installable `src/sekai/` package, dependency management via `uv` (`pyproject.toml` + lockfile).
- **Data contracts:** `RawItem` and `Synthesis` as real types in code (matching the JSON shapes from the PRD), not implicit dicts.
- **Dependency injection:** a `dependency-injector` container constructs the concrete `praw.Reddit` and Anthropic clients. Every stage function takes its dependencies as explicit parameters (e.g. `fetch_reddit(topic, config, reddit_client)`, `synthesize(topic, items, llm_client)`) — no stage constructs a client internally. The CLI entrypoint is the only place the container is resolved.
- **Fetch (minimal):** searches Reddit site-wide (`r/all`) for the topic within a hardcoded 30-day recency window, pulling matching **submissions only** (title + selftext) — no comments yet (that's slice 2). Dedup by `id`/`link`. Reads `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET`/`REDDIT_USER_AGENT` from the environment; fails fast with a clear error before any network call if any are missing.
- **Curate (minimal):** a basic filter (drop empty/too-short text) plus a top-N-by-raw-score selection, where N = `--max-items` (default 15). This is intentionally simpler than the final heuristic — full noise filtering and recency-weighted ranking land in slice 3.
- **Synthesize (basic):** a single call to Claude Haiku (`ANTHROPIC_API_KEY` env var) forcing JSON-only output matching the `Synthesis` contract. Parses the JSON response; on parse failure, raises a clear error (no retry loop yet — that's slice 4).
- **Render:** pure function, `Synthesis` JSON → Markdown string (topic heading, `consensus_ja`, `tensions_ja`, then each view with stance, `summary_ja`, optional `why_surprising`, and source link). CLI writes the string to `--out` (default `report.md`), overwriting on every run, then prints a one-line stdout confirmation (e.g. `Report written to report.md`) — not the full report body.
- **CLI surface:** `--topic` (required), `--sources` (default `reddit`, validated to currently accept only `reddit`, clear error otherwise), `--model` (default `haiku`, validated to currently accept only `haiku`, clear error otherwise), `--max-items` (default 15), `--out` (default `report.md`).
- **Empty/failed Fetch:** if Fetch returns zero items, abort immediately with a specific error message and non-zero exit code — do not call Curate/Synthesize with an empty list.

## Acceptance criteria

- [ ] `uv run sekai --topic "<topic>"` runs end-to-end against real Reddit + Anthropic APIs and produces a `report.md` with a consensus, tensions, and at least one view with a working source link, translated and culturally framed in Japanese.
- [ ] `RawItem` and `Synthesis` are defined as real types in code.
- [ ] All client construction happens only inside the DI container, resolved only at the CLI entrypoint; every stage function receives its dependencies as parameters.
- [ ] Missing Reddit credentials produce a clear error before any network call.
- [ ] An invalid `--sources` or `--model` value produces a clear error instead of proceeding.
- [ ] Zero Fetch results abort the pipeline immediately with a specific error and non-zero exit code, without calling Curate or Synthesize.
- [ ] Malformed JSON from the LLM raises a clear error (retry behavior is out of scope for this slice).
- [ ] An end-to-end test exists that injects a fake Reddit client and a fake Anthropic client into the container and asserts on the final rendered Markdown content.
- [ ] `report.md` is overwritten (not versioned/timestamped) on every run, and a one-line confirmation is printed to stdout.

## Blocked by

None - can start immediately.

