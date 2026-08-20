# Context Mode contract

Context Mode is a hard runtime dependency. Start the Harness/MCP server with `CONTEXT_MODE_PROJECT_DIR=<absolute-agent-root>` and `CONTEXT_MODE_DIR=<absolute-agent-root>/.context-mode`; the latter must be an absolute, Agent-exclusive directory. The installed lifecycle launcher exports the same values, but it cannot retroactively change an already-running MCP server.

For each fresh run:

1. Create the run and verify `.ai-mapper-project` contains the exact canonical Agent root.
2. Call logical `ctx_doctor`; every check must pass within the Harness timeout.
3. Call `ctx_purge(confirm:true, scope:"project")` exactly once.
4. Use the CLI `context-record` command to store one structured receipt containing the logical tool names, success values, diagnostic summary, project purge scope, exact directories, timezone-aware timestamps, and both host call IDs.

The receipt event must precede every query, page fetch, evidence, or candidate-review event. Missing, duplicate, unordered, failed, or directory-mismatched receipts block research and Final Guard. A same-day resume reuses its existing receipt; a cross-day request creates a new run.

If `ctx_doctor` fails, errors, or times out, record one structured failure receipt with `context-record --failed`. This restricted path permits only a `blocked` final status with stop code `CONTEXT_MODE_UNAVAILABLE`; no query, fetch, evidence, or review event may exist.

After Exa responses are persisted, index only the active run's raw results and candidates, then persist the successful host receipt with `context-index-record`. Final Guard requires that receipt after the last query attempt. Add verified pages and candidate cards as they are produced. Synthesize with source-scoped `ctx_search`; do not retrieve prior-run or prior-day indexed content. A mismatched lifecycle environment is a preflight failure, not a warning.

Tool prefixes differ by Harness, so rely on logical names such as `ctx_doctor`, `ctx_purge`, `ctx_index`, and `ctx_search`. When diagnostics cannot pass, stop with `CONTEXT_MODE_UNAVAILABLE`, explain the precise failure and its impact, and provide the relevant Harness installation instructions.
