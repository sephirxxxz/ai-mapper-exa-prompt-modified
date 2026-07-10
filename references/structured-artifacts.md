# AI Mapper Structured Artifacts

Use these alongside Markdown artifacts. Markdown remains the human decision surface; JSONL makes validation and repair deterministic.

## Table of Contents

- [Required Files In Each Workspace](#required-files-in-each-workspace)
- [Status Records For Blocked Runs](#status-records-for-blocked-runs)
- [`research-axes.json`](#research-axesjson)
- [`exa-query-plan.jsonl`](#exa-query-planjsonl)
- [`exa-query-execution.jsonl`](#exa-query-executionjsonl)
- [`exa-candidates.jsonl`](#exa-candidatesjsonl)
- [`candidates.jsonl`](#candidatesjsonl)
- [`evidence.jsonl`](#evidencejsonl)
- [Validation Rules](#validation-rules)

## Required Files In Each Workspace

```text
{WORKSPACE}/research-axes.json
{WORKSPACE}/exa-query-plan.jsonl
{WORKSPACE}/exa-query-execution.jsonl
{WORKSPACE}/exa-candidates.jsonl
{WORKSPACE}/candidates.jsonl
{WORKSPACE}/evidence.jsonl
```

For blocked runs, write the same `record_type: "status"` object directly to `research-axes.json` and as one JSONL row in every required JSONL file. Do not leave these files empty. For complete/degraded runs, every Exa-returned URL must be preserved in `exa-candidates.jsonl`, and every A/B project and talent row must map back to at least one candidate and one evidence object.

## Status Records For Blocked Runs

When a run is blocked before planning, candidates, or evidence can be collected, write one status object to `research-axes.json` and one status row to `exa-query-plan.jsonl`, `exa-query-execution.jsonl`, `exa-candidates.jsonl`, `candidates.jsonl`, and `evidence.jsonl`:

```json
{"record_type":"status","status":"blocked","run_mode":"blocked","blocker_reason":"Exa unavailable","collection_date":"2026-07-07","notes":"No candidate/evidence records were produced."}
```

Required status keys: `record_type`, `status`, `run_mode`, `blocker_reason`, `collection_date`, `notes`. Validator accepts this status record instead of full candidate/evidence keys only when `record_type` is `status`.

## `research-axes.json`

One JSON object containing four mandatory base axes and zero to two enhancement axes. Required top-level keys: `schema_version`, `topic`, `objective`, `collection_date`, `priority_window`, and `axes`.

Every axis requires:

| Key | Meaning |
|---|---|
| `axis_id` | Stable semantic axis id |
| `axis_type` | `base` or `enhancement` |
| `base_role` | One mandatory base role, or `null` for enhancements |
| `label` | Human-readable axis name |
| `ranking_question` | Natural-language description of an ideal result |
| `search_seed` | Stable topic vocabulary without dates/source filters |
| `candidate_types` | Expected entity types |
| `evidence_targets` | Facts original pages should prove |
| `lane_affinity` | One or more A/B/C/D lanes |
| `weight` | `0.1` through `1.0` |
| `exclusions` | Explicit out-of-scope patterns |

The four base roles are `developer-product`, `product-market`, `funding-company`, and `academic-productization`.

## `exa-query-plan.jsonl`

One compiler-generated row per planned Exa query.

Required keys: `schema_version`, `plan_id`, `query_id`, `axis_id`, `lane`, `source_family`, `exa_query`, `ranking_question`, `candidate_types`, `evidence_targets`, `priority`, `run_mode`, `collection_date`, `priority_window_start`, `priority_window_end`, `execution_status`.

Do not hand-edit this file after execution begins. Every `axis_id` must exist in `research-axes.json`.

## `exa-query-execution.jsonl`

One row per executed planned query.

Required keys: `schema_version`, `plan_id`, `query_id`, `axis_id`, `lane`, `source_family`, `exa_query`, `status`, `result_count`, `collection_date`.

Terminal statuses:

- `completed`: at least one usable URL was persisted.
- `queried_no_usable_result`: the query ran but produced no usable URL.

Every plan row must have exactly one terminal execution row before final output.

## `exa-candidates.jsonl`

One JSON object per Exa-returned candidate URL/result before filtering, dedupe, enrichment, or rating. This is the canonical recall audit trail. Lane Markdown queues may be compact review views; this JSONL file must preserve the full Exa return set.

Required keys:

| Key | Meaning |
|---|---|
| `record_id` | Stable local id such as `exa_0001` |
| `plan_id` | Compiled plan id |
| `query_id` | Planned query id |
| `axis_id` | Research axis that produced the query |
| `lane` | `A-dev`, `B-content`, `C-funding`, or `D-academic` |
| `exa_query` | Exact Exa query or source path that returned the URL |
| `query_batch_id` | Batch id tying rows to one Exa request |
| `source_family_planned` | Source family from the query plan |
| `returned_rank` | Rank/index in the Exa response when available |
| `url` | Returned URL exactly as provided |
| `normalized_url` | Canonicalized URL used for dedupe |
| `domain` | URL domain |
| `title` | Returned title |
| `source_type_hint` | Returned/source-inferred type such as repo, funding, product, paper, media, investor |
| `source_family_hint` | Initial source family guess before verification |
| `entry_type_hint` | Lightweight guess: project, person, repo, content, event, paper, funding, investor, product, or unknown |
| `possible_signal` | Lightweight signal: product, funding, team, repo, paper, demo, customer, launch, background, or unknown |
| `risk_reason` | Lightweight risk: stale, duplicate, generic_directory, closed_source, weak_snippet, off_scope, mature, or empty |
| `entity_cluster_id` | Cluster id for likely same project/person/repo across URLs, empty until clustered |
| `must_open_reason` | `official_source`, `funding_source`, `investor_or_vc_source`, `repo_or_model_source`, `paper_or_project_source`, `query_top_result`, `source_family_coverage`, `cluster_representative`, `long_tail_audit`, or `none` |
| `review_decision` | `must_open`, `adaptive_open`, `not_selected`, `defer`, or `blocked` |
| `exa_returned_date` | Exa returned/crawl-like date if present |
| `exa_published_date` | Exa `publishedDate` if present |
| `exa_crawl_date` | Crawl-like date if present |
| `highlight_or_snippet` | Short routing snippet/highlight, not evidence |
| `why_it_might_matter` | Short routing reason for audit and later review |
| `collection_date` | Run date |
| `run_mode` | `adaptive standard scan` or `deep map` |
| `selected_for_review` | Boolean; starts false and becomes true if opened or reviewed |
| `fetch_status` | `pending`, `opened`, `fetched`, `blocked`, `not_selected`, or `not_needed` |
| `keep_drop_status` | `unreviewed`, `kept_raw`, `dropped`, `validated`, `rated`, or `background` |
| `keep_drop_reason` | Why the row was kept, dropped, left unreviewed, or downgraded |
| `candidate_id` | Linked normalized candidate id, empty until resolved |

## `candidates.jsonl`

One JSON object per normalized project/person candidate.

Required keys:

| Key | Meaning |
|---|---|
| `candidate_id` | Stable local id such as `cand_001` |
| `name` | Normalized project/person name |
| `entry_type` | `project`, `person`, `repo`, `content`, `event`, or `paper` |
| `lane` | `A-dev`, `B-content`, `C-funding`, `D-academic`, or `Elsewhere API discovery/supplement` |
| `source_origin` | `Exa`, `Elsewhere API`, or `manual-public-verification` |
| `run_mode` | `adaptive standard scan` or `deep map` |
| `status` | `raw`, `validated`, `rated`, `dropped`, `blocked` |
| `rating` | `A / 重点关注`, `B / 继续观察`, `C / 轻量记录`, `暂不跟进`, or empty before rating |
| `gap_type` | One of the gap enum values in `references/rating-rubric.md` |
| `evidence_ids` | Array of evidence ids supporting the row |
| `notes` | Short uncertainty or dedupe note |

## `evidence.jsonl`

One JSON object per source-backed evidence item.

Required keys:

| Key | Meaning |
|---|---|
| `evidence_id` | Stable local id such as `ev_001` |
| `candidate_id` | Candidate id this evidence supports |
| `url` | Openable URL or Elsewhere URL |
| `source_family` | Source family from `references/source-families.md` |
| `source_type` | product, repo, funding, investor, paper, model, demo, profile, event, media, Elsewhere, etc. |
| `evidence_level` | `S`, `A`, `B`, `C`, or `无效` |
| `claim_supported` | The concrete fact this evidence supports |
| `source_page_date` | Page/article/post/release date or empty if absent |
| `true_event_date` | Real event date used for freshness or empty if not date evidence |
| `exa_returned_date` | Exa returned/crawl-like date if present, never used as freshness evidence |
| `collection_date` | Run date |
| `date_decision` | Which date controls freshness and why |
| `openable_status` | `opened`, `fetched`, `blocked`, `paywall`, `captcha`, `closed`, or `not_needed` |

## Validation Rules

- A/B final rows require at least one non-`无效` evidence object with `openable_status` `opened` or `fetched`.
- A/B final rows require `true_event_date` or a clear `date_decision` explaining why date is not applicable.
- Complete/degraded runs require one `exa-candidates.jsonl` non-status row for every Exa-returned candidate URL counted in the run report's `Total Exa candidate URLs` gate.
- Complete/degraded runs require four mandatory base axes and no more than two enhancement axes.
- Every query plan row must reference a valid axis, and every execution/candidate row must reference a valid query.
- Query quantity gates are counted from terminal `exa-query-execution.jsonl` rows, including `queried_no_usable_result`, not inferred from candidate rows.
- Freehand Exa candidates without `plan_id`, `query_id`, and `axis_id` fail validation.
- Every non-status Exa row must have lightweight triage fields: `entry_type_hint`, `possible_signal`, `risk_reason`, `entity_cluster_id`, `must_open_reason`, and `review_decision`.
- Any row whose `must_open_reason` is not `none` must have `selected_for_review=true` and `fetch_status` of `opened`, `fetched`, or `blocked`.
- Rows with `fetch_status` outside `opened`/`fetched`/`blocked` must not use `keep_drop_status=dropped`; use `not_selected` or `unreviewed` instead.
- Context-mode compression and lane queue compaction cannot justify missing `exa-candidates.jsonl` rows.
- Exa/context-mode snippets cannot be evidence objects unless backtraced to an original public URL.
- Elsewhere-only candidates can be B at most unless original/open project/product/repo/company/funding evidence is also verified.
