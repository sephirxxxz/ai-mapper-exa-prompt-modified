---
description: Run AI Mapper Agent with an optional topic filter.
argument-hint: "[topic]"
---

Context Mode is mandatory. Start the Harness/MCP server with the Agent-isolated `CONTEXT_MODE_PROJECT_DIR` and `CONTEXT_MODE_DIR`, then follow the installed AI Mapper Agent contract in `SKILL.md`, call `ctx_doctor`, and perform the required isolated project purge before research. Treat `$ARGUMENTS` as the optional topic filter for the fixed plan.

Use `$HOME/.claude/bin/ai-mapper-agent` for every lifecycle transition (`create`, `context-record`, `execute-query`, `context-index-record`, `fetch`, `record-browser-fetch`, `review-candidate`, `record-evidence`, `guard`, and `finalize`). Stop with a clear reason if any command returns non-zero.
