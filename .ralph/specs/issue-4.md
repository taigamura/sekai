# Sekai: Curate - full noise-filter + recency-weighted ranking heuristic

> GitHub issue #4 | Labels: ready-for-agent | https://github.com/taigamura/sekai/issues/4

## Parent

#1

## What to build

Replace the skeleton's naive top-N-by-raw-score Curate with the full curation heuristic, so the items reaching Synthesize are genuinely the most relevant and engaged-with, not just whatever has the highest raw score regardless of noise or age.

Curate remains a pure function (no I/O, no LLM call). Two steps:

1. **Noise filter** (hard exclude): drop items that are removed/deleted (e.g. Reddit's `[removed]`/`[deleted]` body), have a null/missing author, or are below a minimum text length (~20 chars).
2. **Rank and trim:** rank surviving items by `score × recency_decay`, where `score` is the Reddit score clamped at 0 (Reddit scores can go negative) and `recency_decay` is exponential with a 48-hour half-life relative to `created_at`. Keep the top N, where N = `--max-items` (default 15).

## Acceptance criteria

- [ ] Items with removed/deleted bodies, missing authors, or sub-20-character text are excluded before ranking.
- [ ] Ranking score is computed as `clamp(score, min=0) × recency_decay(created_at, half_life=48h)`.
- [ ] The top N surviving items (N = `--max-items`) are returned, in ranked order.
- [ ] Pure-function unit tests cover: noise filtering removes the expected items; ranking orders a mix of high-score/old vs. low-score/new items correctly per the decay formula; the N-item cap is respected.
- [ ] No network calls or LLM calls are introduced into Curate.
- [ ] Existing end-to-end test still passes with the new heuristic in place.

## Blocked by

- #2 (skeleton end-to-end pipeline)

