---
name: ai-mapper
description: Use when the user invokes /ai-mapper or asks for AI mapping of early Chinese/China-relevant AI software projects, startups, founders, independent developers, open-source builders, AI product teams, or qualified AI talent leads. Triggers include /ai-mapper, AI mapping, 中文 AI 项目, 中国 AI 创业, 早期项目, AI 人才, AI 融资, Obsidian 报告, source-backed research artifact.
---

# AI Mapper

Create source-backed Obsidian reports for early Chinese/China-relevant AI software projects and qualified talent leads. Every normal run uses `TOPIC=通用扫描`; save artifacts and do not leave the result only in chat.

## Iron Law

Never write final artifacts, update the latest pointer, or call a run `complete` until every mandatory gate is recorded mechanically and both `scripts/forced_pipeline.py guard-final` and `scripts/validate_run.py` pass for the workspace.

## Workflow Checklist

- [ ] Step 0 (⛔ BLOCKING): Setup
  - Resolve paths per `## Paths`.
  - Run `scripts/preflight.py` to classify Elsewhere key/quota, Exa, and context-mode status.
  - Read `references/run-modes.md`, `references/source-policy.md`, and `references/evals.md`.
  - Set `TOPIC=通用扫描`; record any user-emphasized direction in `topic.md` without narrowing the scan.
- [ ] Step 0.6 (⛔ BLOCKING): EXA Query Plan
  - Read `references/exa-query-plan.md`, `references/search-plan.md`, and `references/run-modes.md`.
  - Agent-generate four mandatory base axes plus zero to two enhancement axes in `{WORKSPACE}/research-axes.json`.
  - Base axes must cover developer/product, product/market, funding/company, and academic productization. Enhancement axes may widen user-emphasized or current themes but cannot replace a base axis.
  - Run `scripts/build_exa_query_plan.py compile --workspace "$WORKSPACE" --run-mode "$RUN_MODE"`.
  - Confirm `{WORKSPACE}/exa-query-plan.jsonl` covers all four lanes and meets the selected mode's query floors.
  - After compilation, execute only query rows from `exa-query-plan.jsonl`; freehand Exa recall queries are invalid.
- [ ] Step 1 (⛔ BLOCKING): Exa recall
  - Run four lanes (`A-dev`, `B-content`, `C-funding`, `D-academic`) from the compiled plan.
  - Persist every Exa response through `scripts/forced_pipeline.py record-exa-response --query-plan-file "$WORKSPACE/exa-query-plan.jsonl" --query-id "$QUERY_ID"`.
  - The recorder writes returned URLs to `exa-candidates.jsonl` and every executed query, including zero-result queries, to `exa-query-execution.jsonl`.
- [ ] Step 2 (⚠️ REQUIRED): Candidate triage and opening
  - Tag every row with `source_family_hint`, `entry_type_hint`, `possible_signal`, `risk_reason`, `entity_cluster_id`, `must_open_reason`, `review_decision`.
  - Open/fetch every row whose `must_open_reason` is not `none`.
  - Use `references/source-families.md` for coverage counting.
- [ ] Step 3 (conditional): Elsewhere API enrichment
  - If Elsewhere is available, run keyword intelligence, project discovery, and financing pass per `references/elsewhere-policy.md`.
  - Write `{WORKSPACE}/elsewhere-api-audit.jsonl`.
- [ ] Step 4 (⚠️ REQUIRED): Public-web enrichment
  - For likely A/B projects and all named people, resolve Team, Funding, Product proof, and Date proof from public sources.
- [ ] Step 5 (⚠️ REQUIRED): Validate, enrich, rate
  - Read `references/rating-rubric.md`, `references/schemas.md`, `references/structured-artifacts.md`.
  - Write `validated.md`, `rated.md`, `candidates.jsonl`, `evidence.jsonl`.
- [ ] Step 6 (⛔ BLOCKING): Final guard
  - Run `scripts/forced_pipeline.py guard-final --workspace "$WORKSPACE" --run-mode "$RUN_MODE" --elsewhere-status {available|missing_key|quota_exhausted|rate_limited|error|not_run}`.
  - Run `scripts/validate_run.py --workspace "$WORKSPACE"`.
  - If either fails because selected-mode gates are below minimum while Exa/workspace are available, continue recall/opening; do not write final/latest.
- [ ] Step 7 (⚠️ REQUIRED): Write artifacts
  - Before overwriting `${BASE}/${DATE}-ai-mapper.md` or `${BASE}/最新AI项目与人才Mapping.md`, use `AskUserQuestion` to confirm.
  - Write final report, raw artifact, latest pointer, and run report.
  - Return paths, counts, and limitations only.

## Core Contract

- Use current web/source inspection. Do not use memory for current projects, people, funding, dates, activity, or contact paths.
- Always set `TOPIC=通用扫描` for normal runs.
- Use `TOPIC=通用扫描` for every normal run. Do not ask the user to choose a direction.
- Normal runs are recency-first. Apply the Recency Gate, Priority Objective, Recall Volume Gate, Source Coverage Gate, and Exa Search Quantity Gate from `references/search-plan.md`.
- Default to `adaptive standard scan`; use `deep map` only for the explicit triggers in `references/run-modes.md`.
- Run the Elsewhere Financing Pass when Elsewhere is available and use the standard final/raw/latest paths in every run state.
- Record `true_event_date` separately from source-page and Exa-returned dates.
- Product Hunt, GitHub Trending, and Hugging Face Trending are radar only; backtrace candidates to original evidence.
- Do not create a separate academic talent table.
- Use exactly four raw-search lanes: `A-dev`, `B-content`, `C-funding`, `D-academic`.
- Every normal run uses four mandatory semantic base axes and zero to two enhancement axes. Research axes decide what to investigate; the deterministic compiler decides source-specific Exa queries.
- Exa recall is valid only when every request comes from `exa-query-plan.jsonl` and every planned query has a terminal row in `exa-query-execution.jsonl`.
- Broad discovery uses four raw-search lanes by Main Codex, not four search agents. Subagents may process lane candidates only after the Exa Candidate Queue exists and only if the user explicitly asks for parallel processing.
- Exa recall is only valid after every response is saved to `{WORKSPACE}/exa-candidates.jsonl`. If persistence fails, mark the run `blocked`.
- Elsewhere API is mandatory for `complete` runs. If unavailable, continue as `degraded / Exa-only` with standard paths and explicit status labels.
- Elsewhere is never the team/person/background/contact backfill path. Missing fields must be written as concrete public-web/Codex search gaps.
- Exa summaries, highlights, rank order, and snippets are radar signals only; they become evidence only after backtracing to openable original sources.
- Context-mode is context hygiene only, not evidence or memory.
- Public sources must be directly openable without login, account, QR code, CAPTCHA, or paywall.
- Do not paste large final tables in chat.
- Recruitment/job-board paths are banned as discovery, evidence, contact, or rating signal.
- Main Codex owns setup, recall, validation, rating, final writing, latest pointer, run report, and any Lark/Base mutation.

## Confirmation Gates

Use `AskUserQuestion` before:

- Overwriting `${BASE}/${DATE}-ai-mapper.md` or `${BASE}/最新AI项目与人才Mapping.md` when the file already exists.
- Marking a run `complete` when it is `degraded / Exa-only` or when `guard-final`/`validate_run.py` reported warnings that were resolved by continuing work.

## Scope And Rating

For `TOPIC=通用扫描`, stay inside Chinese/China-relevant AI software: AI Agent, MCP, coding agent, AI office/productivity, agent memory, personal AI, developer tools, workflow integration, agent/coding security, AI infra tied to routing/cost/runtime.

Treat as background unless explicitly requested: broad robotics/embodied AI, broad multimodal/video/3D, overseas-only startups, mature companies, B-round-or-later companies, large financing, big-platform projects, generic media/newsletters/podcasts.

Every rated project lead must answer: `是什么项目`, `为什么值得看`, `已有证据是什么`, `缺什么`, `下一步补全项`. Talent rows answer: `找谁`, `为什么值得看`, `已有证据是什么`, `缺什么`, `下一步补全项`.

Output quality bar:

- A project row must identify the project, explain why it matters now, cite at least one openable original or attributed Elsewhere source, and mark missing fields as `待补`.
- A project row cannot be supported only by one media/report page when team, funding, and product proof are all unresolved.
- B rows must name the exact missing field using the gap enum in `references/rating-rubric.md`.
- Talent rows require named person/team, recent source-backed action, and source-backed background; contact is optional.

Read `references/rating-rubric.md` for A/B/C gates, downgrade rules, and the gap enum. Read `references/examples.md` for row shapes.

## Paths

Use these exact paths:

```bash
BASE="/Users/lixiaoran/ObsidianVault/AI-Mapping"
DATE="$(date +%m%d)"
WORKSPACE="$BASE/runs/ai-mapper-$(date +%Y%m%d-%H%M%S)"
RESULTS="$WORKSPACE/results"
FINAL="$BASE/${DATE}-ai-mapper.md"
RAW_DIR="$BASE/raw"
RAW="$RAW_DIR/${DATE}-ai-mapper-raw.md"
mkdir -p "$RESULTS" "$RAW_DIR" "$BASE"
```

Required artifacts:

```text
{WORKSPACE}/topic.md
{WORKSPACE}/topics.md
{WORKSPACE}/research-axes.json
{WORKSPACE}/exa-query-plan.jsonl
{WORKSPACE}/exa-query-execution.jsonl
{WORKSPACE}/results/A-dev.md
{WORKSPACE}/results/B-content.md
{WORKSPACE}/results/C-funding.md
{WORKSPACE}/results/D-academic.md
{WORKSPACE}/validated.md
{WORKSPACE}/rated.md
{WORKSPACE}/exa-candidates.jsonl
{WORKSPACE}/candidates.jsonl
{WORKSPACE}/evidence.jsonl
{WORKSPACE}/AI项目与人才Mapping.md
{WORKSPACE}/run-report.md
{BASE}/{MMDD}-ai-mapper.md
{BASE}/raw/{MMDD}-ai-mapper-raw.md
{BASE}/最新AI项目与人才Mapping.md
```

Artifact paths are stable across complete, degraded, and blocked runs. Do not create alternate `*-exa-only` filenames.

## Resource Layout

Keep `SKILL.md` as the executable contract.

- Read `references/evals.md` when checking whether this skill should load or auditing behavior.
- Read `references/run-modes.md` and `references/run-modes.json` before Exa recall.
- Read `references/run-states.md` before assigning complete, `degraded / Exa-only`, or blocked status.
- Read `references/exa-query-plan.md` before generating research axes or calling Exa.
- Read `references/source-policy.md` before every run.
- Read `references/search-plan.md` before Exa recall and raw lane processing.
- Read `references/elsewhere-policy.md` when Elsewhere is available or when recording Elsewhere degradation.
- Read `references/source-families.md` before source coverage counting.
- Read `references/structured-artifacts.md` before validation/rating.
- Read `references/rating-rubric.md` before validation/rating.
- Read `references/schemas.md` before writing output artifacts.
- Read `references/examples.md` when examples are needed for row shape or downgrade decisions.
- Read `references/blockers.md` when Exa, Elsewhere, context-mode, or public evidence is missing.
- Read `references/pressure-tests.md` when editing this skill or auditing agent compliance.
- Use `scripts/preflight.py` before broad recall.
- Use `scripts/validate_run.py` after every completed mapping run and after editing the skill package.

## Output Schemas

Read `references/schemas.md` before writing any output artifact. It is the binding schema reference for `validated.md`, `rated.md`, final reports, raw concatenation, latest pointer, and source-quality recap.

Final top-level report must contain complete tables and start with a `运行状态` block: run mode, completeness, Elsewhere status, Exa status, stop reason, and impact.

## Run Report

`run-report.md` must include:

- 完整性状态 for the whole run and for A/B/C/D, `validated.md`, `rated.md`.
- A-class project audit, public-web enrichment pass, true-date audit, field quality, Exa recall quality, Exa candidate audit, triage/open audit, run mode/budget, search quantity gate, recall volume gate, source coverage gate, gate pass/fail table, Elsewhere API quality, output quality gate, public-source limitations, entry-type quality, source-quality recap, final counts, and limitations.

Use the exact gate pass/fail header: `Gate | Required | Actual | Pass? | Notes`. Required gate names: `Total Exa query/source paths`, `Total Exa candidate URLs`, `Total opened/fetched original pages`, `Total raw P0/P1 leads`, `C-funding query/source paths`, `C-funding candidate URLs`, `C-funding opened/fetched pages`, `C-funding raw financing/startup leads`, `Source families`, `C-funding source families`, `Elsewhere financing/startup candidate facts`.

## Completion Response

Answer with completeness status, final report path, raw artifact path, latest pointer path, run report path, A/B/C project counts, talent count, and limitations only after `guard-final` and `validate_run.py` have passed for a complete or valid degraded run, or after a real blocker has been recorded.

For `degraded / Exa-only`, explicitly say Elsewhere was unavailable, standard output paths were used, and team/person/background fields were handled by public-web/Codex search gaps.

## Anti-Patterns

- Hand-transcribing Exa responses instead of persisting them through `record-exa-response`.
- Running freehand Exa recall queries after `exa-query-plan.jsonl` exists.
- Replacing a mandatory base research axis with a user-emphasized enhancement axis.
- Using Exa snippets, summaries, rank order, or returned dates as evidence, freshness, or A/B justification.
- Promoting a candidate because Exa returned it recently when the original page is old or undated.
- Spawning subagents before the Exa Candidate Queue exists or letting them run recall, final writing, or latest-pointer updates.
- Using Elsewhere as the backfill path for team, person, background, contact, funding, product proof, or date verification.
- Treating under-minimum counts as a `blocked` state while Exa/workspace are still available.
- Pasting large final tables in chat instead of returning paths, counts, and limitations.
- Creating alternate `*-exa-only` filenames or private-source review artifacts.
- Skipping public-web enrichment just because Elsewhere is available.
- Letting lightweight triage hypotheses become final writing fields.

## Pre-Delivery Checklist

Before returning a completion response:

- [ ] `SKILL.md` under 500 lines and `quick_validate.py` passes.
- [ ] `guard-final` and `validate_run.py` passed for the workspace.
- [ ] Every Exa response is recorded in `exa-candidates.jsonl`.
- [ ] `research-axes.json` contains all four base roles and at most two enhancement axes.
- [ ] Every planned Exa query has a terminal execution row in `exa-query-execution.jsonl`.
- [ ] Every A/B row maps to at least one candidate record and one non-weak evidence record.
- [ ] No row is marked `dropped` unless it was opened/fetched or explicitly blocked.
- [ ] Final report, raw artifact, latest pointer, and run report exist at the exact paths.
- [ ] No large tables pasted in chat.
- [ ] Run status is correctly labeled `complete`, `degraded / Exa-only`, or `blocked`.
