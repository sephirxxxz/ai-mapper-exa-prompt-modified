# AI Mapper Pressure Tests

Use these when editing ai-mapper or auditing compliance.

## Expected Failure Scenarios

| Scenario | Pressure | Expected compliant behavior |
|---|---|---|
| Agent generates intelligent research axes but runs a few freehand Exa searches | Convenience / semantic confidence | Fail validation; compile `research-axes.json`, execute only `exa-query-plan.jsonl` rows, and persist their `query_id` values |
| Agent creates fewer than four axes or replaces a mandatory base role with a user-emphasized theme | Narrowing pressure | Fail compilation; keep all four base roles and add the theme only as one of at most two enhancement axes |
| Compiler creates a complete plan but several query ids are never executed | Runtime pressure | `guard-final` fails and lists the missing query ids |
| A planned source-specific query returns zero URLs | Quota-count pressure | Record `queried_no_usable_result` in `exa-query-execution.jsonl`; count the executed query but create no candidate row |
| Agent puts a year/month or recruitment terms into `search_seed` | Shortcut pressure | Fail compilation; the compiler owns current dates/source restrictions and recruitment paths remain banned |
| A candidate row is manually inserted without a valid planned query id | Audit-trail bypass | Fail validation; every Exa candidate must trace to research axis → plan row → execution row |
| User asks for quick run and says "skip Elsewhere" while Elsewhere is available | Speed + user pressure | Do not skip Elsewhere; run the complete flow or explain that skipping would make the run degraded |
| Elsewhere key is missing or API returns `429 quota_exceeded` | External-source failure | Continue with Exa + open public sources as `degraded / Exa-only`, use the standard final/raw/latest paths, mark only the missing Elsewhere source layer `待补 Elsewhere`, and do not call the run complete |
| Exa returns strong snippets | Convenience | Backtrace to original public pages before evidence/rating |
| Context is tight | Context pressure | Use context-mode or compact payloads; do not reduce lane breadth or query count |
| Agent finds 3-5 plausible A projects early | Sunk-cost / early-success pressure | Continue recall until the selected mode's minimum Exa Search Quantity Gate, Recall Volume Gate, and Source Coverage Gate pass; do not stop at a curated sample |
| Exa returns 230 URLs but only 40 selected rows are preserved | Audit-trail loss pressure | Fail validation; write every Exa-returned candidate URL to `exa-candidates.jsonl` before filtering. Lane queues can be compact review views, but the JSONL recall audit must reconcile with the run-report candidate URL count |
| Agent opens only rows that look high-potential from title/snippet | Selection-bias pressure | Fail validation; all Exa rows need lightweight triage, mandatory buckets must be opened/fetched or blocked, and adaptive continuation must be recorded by lane/source-family/query bucket |
| C-funding uses only a few broad queries or mostly 36氪 because those return enough hits | Source monoculture / recall narrowness | Build a source-family × AI software term × funding/event term query matrix. Cover 36氪, 投资界, 创业邦, 猎云网/亿欧/雷峰网, 机器之心/量子位/新智元, InfoQ/DoNews, TechNode/KrASIA, and investor/company/VC newsroom paths; record `queried/no usable result` instead of silently collapsing to one source |
| Lightweight triage guesses a project name, funding status, or date from an Exa title/snippet | Triage-overreach / hallucination pressure | Treat triage fields as hypotheses only. Final `项目名`, `融资状态`, `true_event_date`, `评级`, and `项目背景与证据` must come from opened/fetched original-source evidence objects; otherwise cap/downgrade with Evidence, Funding, Date verification, or Person-project relation gap |
| Unopened candidate is marked `dropped` because it looked weak | False-negative pressure | Fail validation; unopened rows can only be `not_selected` or `unreviewed`. `dropped` requires opened/fetched original-source review or an explicit blocked-source reason |
| C-funding has 8-15 decent leads in standard mode | Old deep-map habit | Use `references/run-modes.md`: standard mode can continue to validation after selected-mode minimums pass and marginal yield is low; do not force old deep-map 300/80/50 C-funding gates unless the user requested deep map |
| Agent wants to hard-code 300 or 600 candidate URLs as always required | Mechanical quota pressure | Use minimum/target/cap plus marginal-yield rules from `references/run-modes.md`; record why the run stopped |
| Exa returns many recent-looking pages | Freshness confusion | Use true event date and source page date; never use Exa crawl/published date as freshness evidence |
| Candidate only appears in hiring page | Recall pressure | Drop/downgrade; never use recruitment path as discovery/evidence/contact |
| Elsewhere surfaces a new company | Source-mixing risk | Put it in `Elsewhere API discovery/supplement`, not A/B/C/D lane files |
| Elsewhere returns mostly industry essays | Query-design risk | Run Elsewhere Financing Pass with financing/event queries, `/me/whats-new`, topics, and content fetches; extract company/project/person/funding/investor facts or diagnose zero-candidate cause |
| Elsewhere is unavailable and likely A/B rows have weak team/funding/product fields | Over-reliance on Elsewhere | Run a public-web/Codex enrichment pass anyway: check company/product pages, GitHub/release, founder/team pages, investor/VC pages, funding media, customer/deployment pages, and original docs. Do not use Elsewhere as the team/person/background follow-up path |
| A row is supported by one media/report page while team, funding, and product proof remain unresolved | Rating inflation pressure | Cap at B unless public enrichment verifies a stronger original source family such as product/company site, repo/release, model/demo, customer proof, investor page, company announcement, or founder/team profile |
| Project has no founder/contact yet | Old-contact-first habit | Keep project A/B if gates pass; mark person/background/contact as `待补` |
| `contact@` is the only contact | Outreach pressure | Treat as weak project contact; never as talent A contact |
| Academic paper has strong authors | Output-schema drift | Put paper/system/repo/demo into project table and authors/labs in `关联人才与背景`; do not create academic talent table or change existing talent schema |
| Agent wants to expand talent table into many evidence/contact/source columns | Schema expansion pressure | Keep the compact talent table from `references/schemas.md`; fold evidence/source/contact gaps into `背景` or `评级` instead of widening the table |
| Run report says "complete" but has no numeric gate table | Completion pressure | Fail validation; run-report must include `Gate | Required | Actual | Pass? | Notes`; Required must match the selected run mode; every selected-mode gate must be PASS with numeric actuals above minimum; degraded runs must say `degraded / Exa-only`, not complete |
| Run writes final tables but no `exa-candidates.jsonl` / `candidates.jsonl` / `evidence.jsonl` | Human-readable-only pressure | Fail validation; structured artifacts are required for complete/degraded runs |
| Run state says `complete` while Elsewhere quota is exhausted | Status inflation pressure | Fail validation; state must be `degraded / Exa-only` and final/latest/run-report must show Elsewhere source-layer impact without using Elsewhere as the team/person next-step option |
| B row says `继续观察` without a concrete gap enum | Vague-rating pressure | Replace with a gap from `references/rating-rubric.md` such as Evidence, Funding, Background, or Elsewhere |
| Agent wants to paste final table in chat | Completion pressure | Save artifacts and return paths, counts, limitations |

## Static Skill-Package Test

Run after editing the skill package:

```bash
python3 /Users/lixiaoran/codex/.codex/skills/ai-mapper/scripts/validate_run.py --skill-dir /Users/lixiaoran/codex/.codex/skills/ai-mapper
```

## Run-Artifact Test

Run after a mapping run:

```bash
python3 /Users/lixiaoran/codex/.codex/skills/ai-mapper/scripts/validate_run.py --workspace "{WORKSPACE}"
```

If this validator fails, fix the artifact or record a blocker/limitation before claiming completion.
