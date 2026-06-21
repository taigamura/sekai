# Sekai: Synthesize - retry + grounding loop

> GitHub issue #5 | Labels: ready-for-agent | https://github.com/taigamura/sekai/issues/5

## Parent

#1

## What to build

Add the retry-and-grounding loop to Synthesize, so transient LLM mistakes (malformed JSON, or a fabricated/ungrounded source link) are corrected automatically where possible, and the pipeline fails loudly rather than rendering a broken or fabricated report when they aren't.

Grounding check: every `view.link` in the LLM's response must match a `link` actually present in the curated shortlist passed into Synthesize. A response with any out-of-shortlist link is treated identically to a JSON parse failure for retry purposes — there is no separate "low-confidence" flag or score.

Retry behavior: up to 2 retries (3 attempts total), shared across JSON-parse failures and failed link-validation. Each retry re-sends the original prompt plus the LLM's prior (malformed or ungrounded) output, with an explicit instruction to fix it. If all 3 attempts fail, abort the run with a clear, specific error — never render a partial or fabricated report.

## Acceptance criteria

- [ ] A response with malformed JSON triggers a retry (re-sending the prior output plus a correction instruction), up to 2 retries.
- [ ] A response with valid JSON but a `view.link` not present in the shortlist is rejected and retried using the same retry budget as JSON-parse failures (not a separate budget).
- [ ] After 3 total failed attempts (any combination of parse failure / grounding failure), the run aborts with a clear, specific error and non-zero exit code — no `report.md` is written.
- [ ] A successful retry (e.g. malformed JSON on attempt 1, valid+grounded JSON on attempt 2) completes normally and produces a correct report.
- [ ] Tests using a fake Anthropic client cover: malformed-then-valid (retry succeeds), always-ungrounded-link (exhausts retries, aborts), and always-malformed (exhausts retries, aborts).
- [ ] Existing end-to-end test still passes with the retry loop in place.

## Blocked by

- #2 (skeleton end-to-end pipeline)

