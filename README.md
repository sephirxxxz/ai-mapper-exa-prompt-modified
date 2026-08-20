# AI Mapper Agent

AI Mapper Agent runs inside Codex or Claude Code. It maps early China-relevant AI software projects and public professional talent leads with a fixed Exa search plan, public-page verification, and a local audit trail.

## Runtime contract

- One Agent covers four internal lanes with exactly 40 logical Exa `auto` queries: 10 developer, 8 content, 14 funding, and 8 academic queries. A transient retry is another API request for the same logical query.
- Context Mode is mandatory. A fresh run stops unless `ctx_doctor` succeeds and one isolated project purge is recorded before research.
- Exa execution accepts only a `query_id`; the runtime rebuilds the request from the immutable saved plan. It makes at most three attempts and stores one final query status.
- A maximum of 60 public pages may be fetched. Successful receipts must point to a run-local file with a matching byte count and SHA-256 content hash.
- Every A/B claim links to evidence for the same candidate and claim from a successfully fetched source.
- Candidate review follows `references/rating-rubric.md`; ratings are restricted to `A`, `B`, `C`, and `暂不跟进`, and linked evidence repeats the exact claim text.
- A run becomes `complete` only after non-empty reports and the Final Guard pass. `partial` and `blocked` runs state the stop code, reason, and impact.

## Install

Context Mode must be installed separately in every selected harness. The installer adds AI Mapper discovery files but never changes Context Mode, hooks, plugin trust, or other global plugin settings.

```sh
./scripts/install.sh --codex
./scripts/install.sh --claude
./scripts/install.sh --both
```

By default, Codex is linked under `${CODEX_HOME:-$HOME/.codex}/skills/ai-mapper-agent` and Claude files under `$HOME/.claude`. Each Harness also receives `bin/ai-mapper-agent`, a launcher that works outside the repository directory. For an isolated installation test, pass `--config-root /absolute/path`; this creates `codex/` and `claude/` below that directory. Existing unrelated targets are preserved and cause the installer to stop.

Set `EXA_API_KEY` in the environment before a real run. The offline test suite never calls Exa.

## Run

Invoke `$ai-mapper-agent` in Codex or `/ai-mapper [topic]` in Claude Code. Installed Harnesses use their absolute launcher (`${CODEX_HOME:-$HOME/.codex}/bin/ai-mapper-agent` or `$HOME/.claude/bin/ai-mapper-agent`). Source development can use:

```sh
python3 -m ai_mapper_agent --help
```

The Harness must start its Context Mode MCP server with `CONTEXT_MODE_PROJECT_DIR` equal to the Agent root and `CONTEXT_MODE_DIR` equal to `<agent-root>/.context-mode`. It performs `ctx_doctor` and the isolated purge, then records their structured host receipts with `context-record`; the lifecycle command rejects a mismatched environment. It executes Exa by saved query ID, writes research artifacts only inside `runs/<run_id>/`, indexes current-run Exa results and fetched pages into Context Mode, and uses source-scoped `ctx_search` for synthesis. Use `fetch`, `review-candidate`, and `record-evidence` for the candidate-bearing path.

## Uninstall safety

Normal uninstall removes only local runtime helpers and preserves research data:

```sh
./scripts/uninstall.sh --root /absolute/agent/root --yes
```

Data removal additionally requires `--purge-data --confirm-root /the/exact/canonical/root`. The command refuses roots whose `.ai-mapper-project` marker or `SKILL.md` identity does not match.

## Residual trust boundary

Receipts prove consistency inside the run, not cryptographic authenticity. A local process that can rewrite the repository can also forge files. HTTP fetching pins the validated public IP through the connection while retaining the original Host name and TLS Server Name Indication; every redirect is independently resolved and validated. Run the Agent only in a trusted local environment.

## Local-only status

This worktree is for local development and testing. Do not publish or redistribute it until upstream licensing and contributor authorization are established.
