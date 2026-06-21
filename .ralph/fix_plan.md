# Ralph Fix Plan (queue item)

## Learnings

- GitHub issue #1 (`.ralph/specs/issue-1.md`) is the overarching MVP PRD/epic —
  too large to implement in one loop. It has already been broken down into
  smaller, sequenced issues in the GitHub queue: #2 (skeleton end-to-end
  pipeline), #3 (Fetch: add comments), #4 (Curate: full heuristic), #5
  (Synthesize: retry + grounding loop). Each later issue deepens a stage that
  issue #2 establishes as a minimal-but-real version — implement them in
  order.
- **2026-06-22:** Issue #2 (skeleton end-to-end pipeline) was implemented by
  an earlier loop: `src/sekai/` package (contracts, fetch, curate,
  synthesize, render, container, cli), `pyproject.toml`, and `tests/`
  (end-to-end pipeline test with fake Reddit/Anthropic clients injected via
  DI container overrides, plus pure unit tests for curate/render). Reviewed
  every module and test against the issue-2 acceptance criteria line by
  line this loop — implementation looks correct and complete (DI-only
  client construction, fail-fast credential/validation checks, zero-fetch
  abort, malformed-JSON error, overwriting report.md + one-line stdout
  confirmation).
- **Bug found and fixed this loop:** `README.md` had been written with a
  UTF-16-ish encoding by an earlier loop's Write call — `file README.md`
  reported `data`/binary, and `git diff` showed it as a binary file (every
  character had a stray null byte / rendered as space-separated garbage,
  e.g. "世界" became "NLu)"). Rewrote it as plain UTF-8 with the same
  intended content (setup/credentials/run/test instructions). Spot-checked
  every other staged text file (`file <path>` on all of CLAUDE.md,
  INITIAL_SPEC.md, docs/agents/*, pyproject.toml, src/sekai/*.py,
  tests/*.py, .ralph/specs/*.md) — all are clean ASCII/UTF-8; README.md was
  the only casualty.
- **Environment blocker (still in effect):** this session's Bash permission
  policy (`.claude/settings.local.json`) blocks `uv`, `pip`, `pytest`, and
  any Python execution (`python3 -m ...`) outright — only `git`
  read/commit subcommands, `gh issue/label/auth`, and a few setup one-offs
  are auto-allowed. `uv sync`, `uv lock`, and `uv run pytest` could not be
  run this loop either, so:
  - No `uv.lock` exists yet (spec asks for "pyproject.toml + lockfile").
  - The test suite is still **unverified by execution** — only verified by
    careful manual code review. A human or a loop with broader Bash
    permissions should run `uv sync && uv run pytest` and fix anything
    that doesn't pass.
- Reddit API credentials are still not set up by the developer (per
  `.ralph/specs/issue-1.md`) — blocks live Fetch runs, not code/tests (tests
  use fake clients, no live credentials needed).
- Git identity (`user.name`/`user.email`) is now configured in this
  environment (was the prior loop's commit blocker) — commits succeed now.

## Current Task

- [x] Implement GitHub issue #2 — skeleton end-to-end pipeline (code
      reviewed and committed this loop; README encoding bug fixed;
      **still needs `uv sync && uv run pytest` run by something with Bash
      permission to install deps, generate `uv.lock`, and execute tests**)
- [ ] Next: GitHub issue #3 — Fetch: include top-level Reddit comments
  - Spec: `gh issue view 3 -R taigamura/sekai`
