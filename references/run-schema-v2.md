# Run schema v2

`run-manifest.json` is the authoritative status record. It stores schema and Agent versions, run identity, timezone, fixed-plan hash, Context Mode state, observed cost, final status, stop code/reason/impact, and run-relative artifact paths.

## Query proof

`query-plan.jsonl` contains the deterministic 40 logical queries `q01` through `q40` with lane allocation 10/8/14/8. `query-attempts.jsonl` stores each canonical request, request hash, attempt number, result or error code, and time. A transient retry is another API request for the same logical query; at most three attempts lead to exactly one row in `query-execution.jsonl`. A complete run accepts only `completed` and `zero_results` finals. `raw/exa-responses.jsonl` retains the full successful response and matching request proof. Guard reconciles the successful attempt, raw result count, final status/count, and every candidate URL and rank.

## Web and evidence proof

`candidates.jsonl` retains every returned URL and links duplicates with `duplicate_of`. `fetches.jsonl` is append-only: each successful HTTP or browser receipt names a canonical public URL, method, time, run-relative page path, byte count, and SHA-256 hash. Final Guard recomputes the saved file proof and enforces the 60-page cap.

`evidence.jsonl` binds each evidence ID to one candidate ID and one stable claim ID. Every A/B claim lists at least one evidence ID whose candidate, claim, source URL, exact page excerpt, bounded regex pattern and offsets, content hash, and successful fetch receipt all match.

## Finalization

Required reports are `candidate-cards.md`, `report.md`, and `run-report.md`; all must be non-empty. `complete`, `partial`, and `blocked` statuses require a stop code, human reason, impact, and finalization time. `latest.json` moves only after the status-appropriate Guard passes. `latest-complete.json` moves only for `complete`.

Offline fixtures require `AI_MAPPER_TEST_MODE=1`, mark the manifest permanently, and update only `latest-test.json`. Production Guard rejects these runs even when their internal test status is `complete`.

All mutable research artifacts live below `runs/<run_id>/`. Installed Harnesses use their `bin/ai-mapper-agent` launcher; source development may use `python3 -m ai_mapper_agent`. Run `--help` for current command arguments.
