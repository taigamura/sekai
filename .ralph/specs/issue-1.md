# Sekai MVP: EN-to-JP discourse synthesis CLI (Reddit + Claude Haiku)

> GitHub issue #1 | Labels: ready-for-agent | https://github.com/taigamura/sekai/issues/1

## Problem Statement

A Japanese reader who wants to understand what English-speaking online communities (starting with Reddit) think about a given topic has no easy way to do so. They'd have to read a large volume of English-language posts and comments themselves, then mentally translate and culturally re-contextualize the opinions they find — a slow, language-gated task. Generic translation tools translate text literally but don't synthesize a *spectrum* of opinion (consensus vs. tension vs. surprising takes), don't ground their output in real, checkable sources, and don't frame why a given view might be surprising or notable specifically *for a Japanese reader*.

## Solution

A local command-line tool that takes a topic, fetches recent Reddit discourse (posts and top-level comments) about it, curates the most relevant and engaged-with items, and makes a single LLM call to synthesize the range of opinion — consensus, tensions, and surprising views — translating and culturally framing each for a Japanese reader. The result is rendered as a Markdown report where every view keeps a working link back to its real Reddit source. The tool runs entirely locally, costs fractions of a cent per run, and is built as four independent, contract-conformant stages (Fetch → Curate → Synthesize → Render) so each can be tested and evolved in isolation.

## User Stories

1. As a JP-speaking user, I want to run a single CLI command with a topic, so that I can get a Japanese-language discourse report without manual research.
2. As a user, I want the tool to search Reddit for posts and comments matching my topic, so that the report reflects real, current discourse.
3. As a user, I want the tool to only consider discourse from the last 30 days, so that the report reflects current sentiment rather than stale opinions.
4. As a user, I want noisy, removed, deleted, or too-short Reddit content filtered out before synthesis, so that the LLM isn't synthesizing from garbage input.
5. As a user, I want the most engaged-with and recent items kept (top 15 by default), so that the synthesis focuses on the most representative views rather than being overwhelmed by volume.
6. As a user, I want the synthesis to capture the broad consensus, the points of tension, and at least one surprising or contrarian view, so that I get a balanced sense of the discourse, not just the loudest opinion.
7. As a user, I want every view in the report translated and culturally framed for a Japanese reader, so that I understand not just what was said but why it matters or is surprising in a JP context.
8. As a user, I want every synthesized view to link back to its real Reddit source, so that I can verify the claim and read further myself.
9. As a user, I want the tool to never invent content not grounded in the fetched data, so that I can trust the report as a faithful summary rather than an LLM hallucination.
10. As a user, I want the report rendered as a clean Markdown file, so that I can read it in any Markdown viewer or pipe it into other tools.
11. As a user, I want to choose the output file path via `--out`, so that I can organize multiple reports across topics and runs.
12. As a user, I want a one-line confirmation printed to stdout when the report is written, so that I know the run succeeded without having to open the file.
13. As a user, I want a `--model` flag, so that the LLM backend is explicit and swappable even though Haiku is the only supported option in the MVP.
14. As a user, I want a clear, specific error message and non-zero exit code if Reddit returns zero results for my topic, so that I know to try a different topic rather than receiving a misleadingly empty or garbage report.
15. As a user, I want a clear error message if my Reddit API credentials are missing or invalid, so that I can fix my environment setup quickly.
16. As a user, I want the tool to automatically retry if the LLM's JSON output is malformed, so that a transient formatting mistake doesn't fail my whole run.
17. As a user, I want the tool to reject and retry a synthesis response if any view's source link isn't actually in the curated shortlist, so that the grounding guarantee holds even if the LLM misbehaves.
18. As a user, I want the tool to abort loudly — not produce a partial or fabricated report — if the LLM can't produce valid, grounded JSON after retries, so that I never mistake a broken run for a real report.
19. As a user, I want to control how many items survive curation via `--max-items`, so that I can tune the depth (and cost) of the synthesis call.
20. As a user, I want `--sources` validated up front (currently Reddit-only), so that I get an immediate, clear error on a typo'd source name instead of a confusing downstream failure.
21. As a developer, I want each pipeline stage to be a function with explicitly injected dependencies, so that I can unit test Fetch and Synthesize without hitting real Reddit or Anthropic APIs.
22. As a developer, I want a DI container that wires concrete Reddit/Anthropic clients only at the CLI entrypoint, so that the rest of the codebase has no hidden global state or hardcoded client construction.
23. As a developer, I want Curate and Render to be pure functions, so that I can test their logic with plain fixtures and no mocking at all.
24. As a developer, I want the project installable and runnable via `uv`, so that setup is fast and reproducible across machines.
25. As a developer, I want one end-to-end test that injects fake Reddit/Anthropic clients and asserts on the final rendered report, so that I have a single high-confidence test covering the whole pipeline instead of four separate brittle per-stage mocks.
26. As a developer, I want the data contracts (`RawItem`, `Synthesis`) defined as real types in code, so that stage boundaries are enforced and self-documenting rather than implicit dicts.

## Implementation Decisions

- **Project layout:** installable `src/sekai/` package (not a flat script), with separate modules per stage (fetch, curate, synthesize, render), plus a CLI entrypoint and a DI container module. Dependency management and virtualenv/lockfile via `uv`.
- **Data contracts:** `RawItem` and `Synthesis` defined as real types (e.g. dataclasses/TypedDicts) in code, matching the JSON shapes in the original spec. `RawItem.source` keeps the broader `reddit | bluesky | hn | news` enum for forward compatibility even though only `reddit` is populated in the MVP.
- **Dependency injection:** the `dependency-injector` library provides a container that constructs and wires the concrete `praw.Reddit` and Anthropic clients. Every stage function takes its dependencies as explicit parameters (e.g. `fetch_reddit(topic, config, reddit_client)`, `synthesize(topic, items, llm_client)`) rather than constructing clients internally. The CLI entrypoint is the only place the container is resolved and concrete clients are constructed.
- **Fetch stage:** a single concrete `fetch_reddit(...)` function — no plugin/adapter registry or abstract source interface. Searches Reddit site-wide (`r/all`) for the topic, within a hardcoded 30-day recency window (not a CLI flag), pulling both matching submissions (title + selftext) and their top-level comments (top 10 by score per matching submission, not nested replies). Each becomes its own `RawItem`. Dedup by `id`/`link`. Adding a second source later means adding a new `fetch_*` function and container provider, not building an abstraction now.
- **Reddit auth:** read from `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` environment variables; fail fast with a clear error if any are missing, before attempting any network call.
- **Curate stage:** pure function, no LLM call and no network access. Two steps: (1) noise filter — drop items that are removed/deleted, have a null/missing author, or are below a minimum text length (~20 chars); (2) rank by `score × recency_decay`, where `score` is the Reddit score clamped at 0 (Reddit scores can go negative) and `recency_decay` is exponential with a 48-hour half-life. Keep the top N items, where N = `--max-items` (default 15).
- **Synthesize stage:** single call to Claude Haiku via the Anthropic API (`ANTHROPIC_API_KEY` env var), forcing JSON-only output matching the `Synthesis` contract. Grounding is enforced by validating that every `view.link` in the response actually matches a `link` in the curated shortlist; a response failing this check is treated the same as a JSON parse failure. Up to 2 retries (3 attempts total) shared across JSON-parse failures and failed link-validation — each retry re-sends the original prompt plus the LLM's prior (malformed or ungrounded) output with an explicit correction instruction. If all attempts fail, abort the run with a clear error; never render a partial or fabricated report. There is no separate "low-confidence" flag or score — link-validation against the shortlist is the sole grounding check.
- **Render stage:** pure function, no I/O itself — takes `Synthesis` JSON, returns a Markdown string (topic heading, `consensus_ja`, `tensions_ja`, then each view with its stance, `summary_ja`, optional `why_surprising`, and source link). The CLI writes that string to the `--out` path (default `report.md`), overwriting on every run — no automatic timestamping or versioning, since `--out` already lets the user choose a distinct path per run. On success, the CLI prints a one-line confirmation to stdout (e.g. `Report written to report.md`), not the full report body.
- **CLI surface:** `--topic` (required), `--sources` (default `reddit`; validated to currently accept only `reddit`, erroring clearly otherwise — kept as a flag now so adding a second source later doesn't require a CLI interface change), `--model` (default `haiku`; this is a deviation from the original spec draft, which had defaulted to `qwen` before the model choice was resolved), `--max-items` (default 15), `--out` (default `report.md`).
- **Empty/failed Fetch:** if Fetch returns zero items (no matching discourse, Reddit auth failure, or rate limiting), the pipeline aborts immediately after the Fetch stage with a specific error message and non-zero exit code. It does not continue into Curate/Synthesize with an empty list.
- **Scope reduction from original spec draft:** Bluesky, Hacker News, and News RSS are dropped entirely from this MVP's deliverables and acceptance criteria — not listed as stretch goals. Local Qwen/Ollama is likewise dropped as a synthesis backend option for this MVP; Haiku is the only supported model.

## Testing Decisions

- Framework: `pytest`.
- A good test in this codebase asserts on a stage's external behavior — its return value, the error it raises, or (for the end-to-end test) the final rendered report content — never on internal implementation details like which internal helper was called.
- **Two seams**, both at the DI-injected client boundary, since those are the pipeline's only two points of contact with the outside world:
  1. A fake `praw.Reddit`-shaped client returning canned submissions/comments, for exercising Fetch.
  2. A fake Anthropic-shaped client returning canned JSON (including deliberately malformed JSON and JSON with an out-of-shortlist link, for retry/grounding tests), for exercising Synthesize.
- **One end-to-end orchestration test** injects both fakes into the container and runs the full `topic → report.md` pipeline, asserting on the final rendered Markdown (consensus present, tensions present, views present with real links) — this is the highest-leverage test, preferred over four separate per-stage mock-heavy tests.
- **Pure-function tests, no mocking needed:** Curate's ranking/filtering logic, given canned `RawItem` fixtures, asserting on filtering and ordering. Render's Markdown formatting, given canned `Synthesis` JSON fixtures, asserting on the output string's structure.
- **Targeted tests around the retry/grounding loop:** fake Anthropic client returns malformed JSON then valid JSON across successive calls (retry succeeds); fake client returns a response with an out-of-shortlist link on every attempt (exhausts retries, pipeline aborts with a clear error); fake Reddit client returns zero items (pipeline aborts after Fetch without calling Synthesize).
- No live-API integration tests in the automated suite (not even an opt-in, credential-gated one) — flaky and costly to maintain for this project. The spec's "3-5 test topics produce a coherent report" acceptance check remains a manual pass run by the developer once Reddit credentials exist; it is not encoded as an automated test.

## Out of Scope

- Bluesky, Hacker News, and News RSS source adapters — no CLI support, no fetch implementations.
- Multi-language support beyond EN→JP.
- Cloud deployment, web UI, mobile clients.
- Video, audio, or tweet rendering — Markdown is the only renderer.
- Paid sources (e.g. X/Twitter) and real-time/streaming ingestion.
- Local Qwen/Ollama as a synthesis backend.
- LLM-assisted relevance ranking in Curate (heuristic-only for this MVP).
- A separate low-confidence/confidence-scoring mechanism in Synthesize output.
- Automatic output file versioning or timestamping.
- Live-API integration tests in CI or the local test suite.
- A `--recency-window` CLI flag (hardcoded constant for this MVP).
- Evaluating or swapping the DI container library — `dependency-injector` is the final choice for this MVP, not a placeholder for comparison.
- Nested reply threads beyond top-level comments.

## Further Notes

- Reddit API credentials (`REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET`/`REDDIT_USER_AGENT`) are not yet set up by the developer. This is an external setup action, not a code blocker for implementing/reviewing this PRD, but it does block actually running Fetch against live Reddit until resolved.
- This PRD supersedes the "Open Decisions" section of `INITIAL_SPEC.md` in this repo — all four items listed there (sources, LLM choice, curation heuristic, defaults) are resolved above. Where this PRD's decisions conflict with details elsewhere in `INITIAL_SPEC.md` (e.g. the CLI table's old `qwen` default, the Bluesky deliverable), this PRD is authoritative.
- A short README with setup and run instructions (including Reddit app registration steps and `ANTHROPIC_API_KEY` setup) remains a deliverable per the original spec, but its exact content wasn't separately interrogated — standard install/run instructions apply.

