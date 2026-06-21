# Sekai: Fetch - include top-level Reddit comments

> GitHub issue #3 | Labels: ready-for-agent | https://github.com/taigamura/sekai/issues/3

## Parent

#1

## What to build

Extend the Fetch stage to pull top-level comments alongside submissions, so the pipeline draws on Reddit's actual discourse (where opinions and disagreement usually live) rather than just post titles/bodies. No other stage changes — Curate, Synthesize, and Render already operate on a general `List[RawItem]` regardless of where each item came from.

For each Reddit submission matching the topic search (within the existing 30-day window), also fetch its top 10 top-level comments by score (not nested replies). Each comment becomes its own `RawItem` (`text` = comment body, `source` = `reddit`, plus the comment's own score/author/created_at/link). Apply the same dedup-by-`id`/`link` as submissions.

## Acceptance criteria

- [ ] Fetch returns `RawItem`s for both matching submissions and their top-level comments (top 10 per submission, by score).
- [ ] Nested/reply comments are not fetched — only top-level comments under a matching submission.
- [ ] Comment `RawItem`s are deduplicated against submissions and each other by `id`/`link`, consistent with existing submission dedup.
- [ ] Running the CLI end-to-end on a topic with active comment threads produces a report whose views are drawn from a mix of submissions and comments (verified via the existing end-to-end test using a fake Reddit client returning both submissions and comments).
- [ ] A unit test confirms the top-10-per-submission comment limit is enforced.

## Blocked by

- #2 (skeleton end-to-end pipeline)

