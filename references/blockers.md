# AI Mapper Blockers

Use these when a normal ai-mapper run cannot meet the contract.

## Table of Contents

- [Under-Minimum Gates Are Not A Blocker](#under-minimum-gates-are-not-a-blocker)
- [Elsewhere API Missing Or Unavailable](#elsewhere-api-missing-or-unavailable)
- [Exa Unavailable](#exa-unavailable)
- [Context-Mode Unavailable](#context-mode-unavailable)
- [Public Evidence Gap](#public-evidence-gap)

## Under-Minimum Gates Are Not A Blocker

Trigger: `guard-final` reports selected-mode quantity or coverage gates below minimum, such as too few Exa query/source paths, candidate URLs, opened/fetched pages, source families, C-funding candidates, or raw P0/P1 leads.

Action:

- If Exa is available and the workspace can still be written, continue Exa recall, persistence, lightweight triage, and mandatory opening.
- Do not write final/latest pointer artifacts.
- Do not mark the run `blocked` merely because current counts are below minimum.
- Do not rewrite `exa-candidates.jsonl`, `candidates.jsonl`, or `evidence.jsonl` to status-only if they already contain real audit rows.
- Partial evidence may be kept in lane notes, but it is not a deliverable state.

Template:

```markdown
## Work Still In Progress - Minimum Gates Not Met

- 状态: continue, not blocked
- 原因: selected-mode recall/open gates below minimum while Exa/workspace remain available
- 当前差距: {gate actuals vs minimums}
- 下一步: continue Exa recall, record every response, then open mandatory buckets
- 禁止: final/latest update, status-only JSONL rewrite, or blocked delivery based only on under-minimum counts
```

## Elsewhere API Missing Or Unavailable

Trigger: no `els_live_...` key is found from `ELSEWHERE_KEY` or `~/.config/elsewhere/key`, or Elsewhere returns quota/rate exhaustion such as `429 quota_exceeded`.

Action:

- Do not mark the run `complete`.
- If Exa is available, continue with Exa + open public sources as `degraded / Exa-only`.
- Write all standard output paths: `{BASE}/{MMDD}-ai-mapper.md`, `{BASE}/raw/{MMDD}-ai-mapper-raw.md`, and `{BASE}/最新AI项目与人才Mapping.md`; do not create alternate `*-exa-only` filenames.
- Put the Elsewhere status and impact in `topic.md`, `topics.md`, final report, latest pointer, and `run-report.md`.
- Mark missing keyword intelligence, discovery/supplement, financing/startup facts, and ecosystem context as `待补 Elsewhere`. Team/person/background/contact fields must use public-web/Codex search gaps, not Elsewhere backfill wording.
- If Exa is also unavailable, write a blocked report in the standard paths and return the blocker.

Template:

```markdown
## Elsewhere API Unavailable - Degraded Run

- 状态: degraded / Exa-only
- 原因: {no `els_live_...` key found / quota exhausted / rate limited}
- 已检查: `ELSEWHERE_KEY`, `~/.config/elsewhere/key`, availability preflight
- 输出路径: standard ai-mapper paths used; no alternate `*-exa-only` files
- 已完成: Exa recall, public-source verification, raw/validated/rated/final artifacts as available
- 未完成: Elsewhere keyword intelligence, Elsewhere discovery/supplement, Elsewhere Financing Pass
- 影响: Elsewhere source-layer context is missing; team/person/background fields still require public-web/Codex search
- 下一步: after quota/key recovers, rerun Elsewhere source checks if needed; use public-web/Codex search to repair team/person fields.
```

## Exa Unavailable

Trigger: Exa broad recall cannot run.

Action:

- Do not fall back to direct web/source search for front-stage A/B/C/D sourcing.
- Record the blocker in `run-report.md`.

Template:

```markdown
## Blocker - Exa Recall Required

- 状态: blocked
- 原因: ai-mapper requires Exa for front-stage A/B/C/D candidate recall.
- 已完成: Elsewhere keyword intelligence/discovery if available in this run
- 未完成: Exa Candidate Queue, lane raw files, validated/rated/final complete output
- 下一步: restore Exa access and rerun broad recall.
```

## Context-Mode Unavailable

Trigger: context-mode tools are absent or fail.

Action:

- Continue with compact Exa payloads and original-source verification.
- Do not reduce query count, candidate URLs, or lane breadth.
- Record the limitation in `run-report.md`.

Template:

```markdown
## Limitation - Context-Mode Unavailable

- 状态: continued
- 影响: no indexed candidate queue or fetched-page search
- 补救: preserved Exa recall breadth and opened original public sources directly
- 禁止: reducing `numResults`, skipping candidate URLs, or shrinking lanes to save context
```

## Public Evidence Gap

Trigger: a candidate depends on closed/account-only sources and no equivalent public or Elsewhere evidence exists.

Action:

- Downgrade to `暂不跟进 / 公开证据不足` or drop.
- Do not ask the user for private access.

Template:

```markdown
## Public Evidence Gap

- 候选: {name}
- 问题: key claim depends on closed/account-only source
- 已查公开来源: {sources checked}
- Elsewhere 结果: {found / not found / conflict}
- 处理: {downgraded / dropped}
```
