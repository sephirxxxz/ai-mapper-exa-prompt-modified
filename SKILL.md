---
name: ai-mapper-agent
description: Use when mapping early Chinese or China-relevant AI software projects, product teams, open-source builders, founders, or public professional talent leads.
---

# AI Mapper Agent

Create one source-backed local research run. A topic narrows the fixed plan; it never creates another search mode or extra query.

## Run sequence

1. Start the Harness/MCP server with `CONTEXT_MODE_PROJECT_DIR` set to the absolute Agent root and `CONTEXT_MODE_DIR` set to `<agent-root>/.context-mode`; the installed launcher exports the same values for lifecycle subprocesses.
2. Resolve the installed launcher: `${CODEX_HOME:-$HOME/.codex}/bin/ai-mapper-agent` in Codex or `$HOME/.claude/bin/ai-mapper-agent` in Claude Code. Run its `create` command; it writes the immutable 40-row plan and returns `run_id`.
3. Call the Harness's logical `ctx_doctor`. Continue only when every diagnostic passes. For the fresh run, verify `.ai-mapper-project`, then call `ctx_purge(confirm:true, scope:"project")` exactly once.
4. Record the structured host call IDs, timestamps, diagnostic summary, project root, and isolated Context directory through the launcher's `context-record` command. Research begins only after this command succeeds. When doctor fails, use `context-record --failed`, write the three blocked reports, and finalize with `CONTEXT_MODE_UNAVAILABLE` without any research.
5. Execute `q01` through `q40` with the launcher's `execute-query --query-id <id>`. The runtime loads the saved request; supply no freehand payload. These are 40 logical queries; transient retries can produce additional API requests.
6. Index current-run Exa responses and candidate records with `ctx_index`, then record that host call with `context-index-record`. Use `ctx_search` to organize only this run's material. Fetch promising public pages with `fetch` or a Harness browser, registering browser-saved pages with `record-browser-fetch`.
7. Read [the rating rubric](references/rating-rubric.md), review every unique candidate with `review-candidate`, and build claim-specific evidence with `record-evidence`. The evidence command attaches its ID to the matching claim. Index current-run candidate cards and verified pages, then use source-scoped `ctx_search` for final synthesis.
8. Write non-empty `candidate-cards.md`, `report.md`, and `run-report.md` with the run summary, candidate counts, stop reason, and artifact paths. Finish through the launcher's `finalize` command, then run `guard`. Return the status, stop reason, counts, observed cost, and artifact paths.

Run the installed launcher with `--help` for exact arguments. In source development, `python3 -m ai_mapper_agent` is the equivalent entry point. Lifecycle state changes use this CLI; the Harness writes candidate review and report content, and Final Guard validates their schema and evidence links.

## Stop conditions

Context Mode is a hard dependency. When `ctx_doctor` is absent, fails, or times out, finalize as `blocked` with `CONTEXT_MODE_UNAVAILABLE`; state the diagnostic failure, its impact, and the Codex or Claude Code installation steps. Exa authentication, credit exhaustion, or unrecoverable request failures produce `partial` or `blocked` with an equally explicit reason and impact.

## Research invariants

- Use exactly 40 Exa `auto` searches: A-dev 10, B-content 8, C-funding 14, D-academic 8. Each requests 10 results within the saved 30-calendar-day publication window.
- Retain every complete Exa response. Highlights route investigation; opened public pages support claims.
- Fetch no more than 60 public pages. Respect access controls and network safety checks.
- A/B claims link to evidence for the same candidate and stable claim ID. Each evidence record includes its public URL, fetch time, exact page excerpt, bounded regex rule and match offsets, and SHA-256 content hash.
- Candidate ratings are exactly `A`, `B`, `C`, or `暂不跟进`; A/B claim text must exactly match the linked evidence claim text.
- `complete` has no candidate-count quota. It requires all process gates, one final status per query, reviewed unique candidates, non-empty reports, and correct latest pointers.

## Current-run Context Mode

The project purge makes the fresh run's Context index empty before Exa material enters it. Index only files from the active `run_id`; current-day material must never be mixed with prior-run or prior-day content. Same-day resume uses the existing run and receipt instead of purging a second time. If the Harness/MCP server was not started with the exact isolated environment, `context-record` must fail and the run must be blocked.

Read [the Context Mode contract](references/context-mode-contract.md) before preflight and [run schema v2](references/run-schema-v2.md) before writing research artifacts.
