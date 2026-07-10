# AI Mapper Search Plan

Read this before Exa recall and raw lane processing.

## Table of Contents

- [Search Plan](#search-plan)
- [EXA Query Plan Gate](#exa-query-plan-gate)
- [Recency Gate](#recency-gate)
- [Priority Objective](#priority-objective)
- [Recall Volume Gate](#recall-volume-gate)
- [Source Coverage Gate](#source-coverage-gate)
- [C-funding Exa Query Matrix](#c-funding-exa-query-matrix)
- [Query Preparation](#query-preparation)
- [Exa Targets And Lead Types](#exa-targets-and-lead-types)
- [Raw Search](#raw-search)

## Search Plan

Always set `TOPIC=通用扫描`. Do not ask the user to choose a direction. If the user names a field such as AI客服、AI办公自动化、MCP应用、AI Agent, or AI教育, record it in `topic.md` as `用户强调方向`, but keep the four-lane generic scan.

Write `topic.md`, then create the four mandatory semantic base axes and zero to two enhancement axes in `research-axes.json` per `references/exa-query-plan.md`. Render the same axes plus Elsewhere Keyword Intelligence into `topics.md` for human review. The four base axes cover developer/product, product/market, funding/company, and academic productization. Enhancement axes may widen a user-emphasized direction or current high-value theme but cannot replace a base axis.

Each axis combines:

- direction terms: `AI Agent`, `MCP`, `Coding Agent`, `browser agent`, `computer use`, `Figma to code`, `原型转代码`, `vLLM`, `模型路由`, `Agent memory`, `prompt injection`, `企业数据`
- early-action terms: `近30天`, `本月`, `最新融资`, `完成融资`, `天使轮`, `种子轮`, `Pre-A`, `内测`, `求反馈`, `我做了一个`, `独立开发`, `创业组队`, `招募用户`, `发布`, `上线`
- talent terms: `GitHub`, `开源`, `论文`, `顶会`, `引用`, `黑客松`, `演讲`, `作者`, `创始人`, `核心开发者`
- source pack and expected entry types: `person`, `project`, `repo`, `content`, `event`, `paper`

## EXA Query Plan Gate

Before the first Exa request:

1. Write `{WORKSPACE}/research-axes.json`.
2. Run `scripts/build_exa_query_plan.py compile --workspace "$WORKSPACE" --run-mode "$RUN_MODE"`.
3. Inspect `{WORKSPACE}/exa-query-plan.jsonl` for four-lane coverage and selected-mode floors.
4. Execute only compiled query rows.
5. Persist every response with `record-exa-response --query-plan-file ... --query-id ...`.

The agent owns `ranking_question`, `search_seed`, evidence targets, lane affinity, and exclusions. The compiler owns dates, source restrictions, variants, query ids, and lane counts. Do not hand-write or improvise additional Exa recall queries after compilation. If a new semantic direction is required, revise `research-axes.json`, recompile before execution begins, and preserve the new plan as the canonical plan.

`ranking_question` is the natural-language ideal-result description. `exa_query` is the source-specific retrieval string. Neither is evidence.

### Recency Gate

Before broad recall, compute the run-date windows and write them into `topic.md`:

- `priority_window`: run date minus 30 days through run date.
- `observation_window`: run date minus 60 days through run date, excluding `priority_window`.
- `background_window`: anything older than 60 days unless there is a new event inside `priority_window`.

For every kept candidate, separate and record the dates in raw notes, `validated.md`, `rated.md`, and `run-report.md`:

- `source_page_date`: article/page/post/release page date.
- `true_event_date`: financing, launch, release, paper acceptance/posting, repo release, model upload, customer/deployment, or other real event date.
- `exa_returned_date`: Exa `publishedDate` or crawl-like date if present.
- `collection_date`: run date.
- `date_decision`: which date was used for freshness and why.

Never promote a candidate because Exa returned it as recent. If the original page is old, undated, or only newly crawled, downgrade or keep it as background unless another openable source proves a recent true event.

### Priority Objective

The scan optimizes for `最近、最新、最值得` plus `未来潜在 candidate`, in that order:

- P0: true event inside the priority window and strong project/person signal, especially new financing, launch, product release, repo/model release, demo day, customer/deployment, founder post, or Elsewhere-reported market event.
- P1: future-potential candidate: no financing yet or incomplete background, but early product/repo/paper-system/team signal is strong enough that it should stay in `validated.md` for later enrichment.
- P2: context/background: mature, late-stage, big-platform, stale, closed-source-only, or useful only for market map.

Do not optimize for a tiny final A list. Keep enough P0/P1 candidates through raw and validated so the final A/B decision table is a ranked market map, not a hand-picked sample. If many rows pass A/B gates, include them; do not cap A merely because the table is long.

### Recall Volume Gate

A normal `通用扫描` uses `adaptive standard scan` by default, not the old 600-candidate deep-map gate. Read `references/run-modes.md` before Exa recall and write the selected `run_mode` into `topic.md` and `run-report.md`.

Default standard scan budgets are minimum / target / cap, not a single hard number: total Exa query/source paths `36 / 40-70 / 80`, candidate URLs `160 / 180-320 / 350`, opened/fetched original pages `50 / 60-100 / 120`, and raw P0/P1 leads `30 / 35-70 / 80`. C-funding stays the highest-weight lane, using the lane allocation in `references/run-modes.md`.

Use `deep map` budgets only when the user explicitly asks for `深度扫`, `全量市场地图`, `重扫一遍`, `尽可能不要漏`, or equivalent high-recall language. Deep map keeps the old high-recall shape: candidate URLs about `500-600`, opened pages about `150-180`, and raw leads `100+`.

After the selected mode's minimum gates pass, Main Codex may stop before the target/cap only when the `Early Stop Rule` in `references/run-modes.md` passes. Record the marginal-yield batch size, new P0/P1 count, duplicate/stale/out-of-scope pattern, and stop/continue decision in `run-report.md`. Do not stop before minimum gates pass, and do not shrink recall merely to save context. If the current count is below minimum, the only valid next action is more recall/opening or documenting a real external blocker; partial evidence is not a deliverable state.

### Source Coverage Gate

The scan must cover enough independent source families according to the selected run mode. Default `adaptive standard scan` requires at least 10 distinct open source families across the four lanes and at least 6 funding/venture source families in `C-funding`; targets are 12-16 and 6-8. `deep map` requires at least 18 source families and at least 10 funding/venture source families. Count source families such as Elsewhere API, 36氪, 投资界, 创业邦, 猎云网, 亿欧, 雷峰网, 新智元, 量子位, 机器之心, InfoQ, DoNews, TechNode, KrASIA, VC newsroom/portfolio pages, company announcements, GitHub, Product Hunt, Hugging Face, arXiv/OpenReview/Semantic Scholar/OpenAlex, demo-day/accelerator pages. If a source family is queried but yields no openable candidates, record `queried/no usable result` instead of silently ignoring it.

### C-funding Exa Query Matrix

`C-funding` must be generated from a query matrix, not a few hand-written broad queries. Main Codex must combine source families, AI software terms, and funding/event terms into source-specific Exa queries before broad recall. Do not let 36氪 dominate the lane merely because it returns many results.

Source-family terms:

- Chinese venture/media: `36氪`, `投资界`, `创业邦`, `猎云网`, `亿欧`, `雷峰网`, `新智元`, `量子位`, `机器之心`, `InfoQ`, `DoNews`
- English/overseas China tech: `TechNode`, `KrASIA`
- Original/near-original funding sources: `company announcement`, `investor portfolio`, `VC newsroom`, `accelerator demo day`, `roadshow`, `incubator`

AI software terms:

- `AI Agent`, `企业级智能体`, `Agent OS`, `Coding Agent`, `AI 编程`, `AI office`, `AI 办公`, `AI 表格`, `workflow automation`, `MCP`, `AI 软件应用`, `AI infra`, `模型路由`, `RAG`, `数据智能体`, `AI 搜索`, `Agent memory`, `prompt injection`, `agent security`

Funding/event terms:

- `融资`, `完成融资`, `获融资`, `天使轮`, `种子轮`, `Pre-A`, `A轮`, `首发`, `独家`, `投资方`, `领投`, `跟投`, `创始人`, `创业`, `发布`, `上线`, `内测`, `商业化`, `客户案例`

For adaptive standard scan, `C-funding` must run at least 12 source-specific query/source paths and should target 14-22, covering at least 6 usable funding/venture source families. At least one query must target each high-value family when Exa is available: 36氪, 投资界, 创业邦, 猎云网/亿欧/雷峰网, 机器之心/量子位/新智元, InfoQ/DoNews, TechNode/KrASIA, and investor/company/VC newsroom pages. If a source family returns no openable candidates, record `queried/no usable result` in `run-report.md` and continue the matrix rather than collapsing back to 36氪-only recall.

Example query templates:

```text
site:36kr.com AI Agent 企业级智能体 融资 天使轮 种子轮 2026 7月 创始人 投资方
site:pedaily.cn AI 软件应用 AI Agent 融资 天使轮 种子轮 2026 7月
site:cyzone.cn AI Agent Coding Agent 融资 创业 2026 7月
site:lieyunwang.com AI 软件 智能体 融资 2026 天使轮 Pre-A
site:iyiou.com AI office AI办公 智能体 融资 创业 2026
site:leiphone.com AI Agent AI软件 应用 创业 融资 2026
site:jiqizhixin.com AI Agent Coding Agent 创业 融资 产品发布 2026
site:infoq.cn AI Agent AI infra 模型路由 创业 融资 2026
site:donews.com AI Agent AI办公 融资 创业 发布 2026
site:technode.com China AI agent startup funding seed round July 2026
site:kr-asia.com China AI software startup funding AI agent seed round July 2026
AI Agent startup funding China investor portfolio newsroom July 2026 seed angel
```

### Query Preparation

The agent prepares 4-6 research axes whose `ranking_question` describes the ideal page, not just keywords. `scripts/build_exa_query_plan.py` deterministically compiles those axes into source-specific Exa rows. Each lane covers candidate discovery, project/product/repo signal, recent activity, true event date, and then contact/background backtracing when possible. Broad recall must use a candidate-queue payload, not page-body payload: prefer `web_search_advanced_exa` with `enableSummary: false`, no subpages, `highlightsMaxCharacters` capped to a small routing snippet, and `textMaxCharacters` set to a very small positive value such as `1` rather than `0` because some providers treat `0` as unlimited/default. Use `web_search_exa` only for narrow spot checks where a long result cannot threaten context. Keep the payload compact, but preserve recall breadth: do not lower result counts, skip query variants, or omit candidate URLs merely to save context. Use context-mode indexed fetching for reading the best returned URLs when highlights are insufficient. Use `web_fetch_exa` only as a last-mile verifier with `maxCharacters` capped and small URL batches; never use it to bulk-open lane candidates into chat. In either case, the original public page is the evidence, not the summary layer. If Exa is unavailable, pause broad discovery and record the blocker in `run-report.md`; do not fall back to direct web/source search for front-stage sourcing.

## Exa Targets And Lead Types

Use Exa to find early projects/products/repos/paper-systems with concrete AI software activity, and use Elsewhere API in parallel as mandatory China tech/venture context and discovery support. Responsible actor, founder, maintainer, background, and contact are enrichment targets after a project is found; they are not prerequisites for project discovery or project-level A. The rows below are query targets and post-recall verification roles, not independent lane-processor search starting points.

| Purpose | Exa target / post-Exa role |
|---|---|
| Exa Radar | `mcp__exa.web_search_exa`, `mcp__exa.web_search_advanced_exa`, `mcp__exa.web_fetch_exa` for broad open-web recall, source/date filters, and first-pass candidate URLs |
| Context Hygiene | `mcp__context_mode.ctx_index`, `ctx_fetch_and_index`, `ctx_search`, `ctx_execute` for storing/querying Exa candidate queues and fetched original pages without dumping raw payloads into conversation context |
| Elsewhere API | Main Codex only; `elsewhere.news/api/v1` connected mode for first-hand China tech/venture reporting, semantic chunks, content detail, entity cards, and relationship edges. Use as an attributed data source for keyword intelligence, project discovery, financing/startup facts, and ecosystem context; never as an Exa lane and never as the required team/person/background backfill path. |
| Public community/product radar - allowlist only | Product Hunt launches, GitHub/GitHub Trending/GitHub releases, Hugging Face Trending/models/spaces/datasets, plus ModelScope/Gitee public project pages only when directly openable and tied to a concrete repo/model/project |
| Funding/venture discovery - open only | 36氪, 投资界, 创业邦, 猎云网, 亿欧, 雷峰网, 新智元, 量子位, 机器之心, InfoQ, DoNews, TechNode, KrASIA, company announcements, investor/VC portfolio pages, VC newsroom pages, and public synchronized article pages that are directly openable without login/CAPTCHA |
| Academic discovery - open only | arXiv, OpenReview, Semantic Scholar, OpenAlex, Papers With Code, ACL Anthology, CVF, NeurIPS/ICLR/ICML proceedings, project/repo/demo pages linked from papers, public lab pages |
| Verification | product site, GitHub repo, Hugging Face page, paper page, author page, company page, funding article, investor page, event page |
| Enrichment | founder/GitHub/public X profiles, personal sites, product/company pages, investor portfolio public pages, paper author/lab pages, Semantic Scholar/OpenAlex profiles |
| Ranking/Index | Only open public radar from Product Hunt, GitHub Trending/repo/release velocity, and Hugging Face Trending/models/spaces/datasets. Exclude broad榜单数据库, generic AI tool directories, generic community feeds, and sources requiring login/account/paywall/CAPTCHA. |

These source roles classify what Exa returns and where evidence is verified; they do not authorize lane processors to run independent candidate discovery. Broad raw lane search starts with Exa Radar, then backtraces kept Exa candidates through openable Public Discovery, Verification, Enrichment, Funding/venture, Academic, and the narrow public radar allowlist above. Context Hygiene may store and query the Exa Candidate Queue or fetched candidate pages, but it never creates candidates outside Exa and never becomes a cited evidence source. Elsewhere API is mandatory and is the exception as a Main-Codex-operated data source: it provides keyword intelligence, discovers source-backed project/person candidates, and adds attributed financing/market/ecosystem facts. Team/person/background/contact fields must still be resolved or marked as unresolved through public-web/Codex search, not an Elsewhere backfill option. Elsewhere candidates stay in the `Elsewhere API discovery/supplement` pool and must not be counted as a fifth raw-search lane or written into lane result files. Discard sources that require an account, private app state, private browser session, QR code, paywall, or CAPTCHA to search or view. If a lane processor finds a promising source outside the Exa queue, it must request Main Codex handling before using it as a candidate. Record Exa usage, Elsewhere usage, context-mode usage, and extra public verification sources in 来源质量复盘.

Use Product Hunt, GitHub Trending, and Hugging Face Trending only as radar for product names, category timing, launch/release velocity, open-source momentum, and competing products. Do not use broad rankings/tool directories/community heat as discovery or rating inputs. Backtrace every candidate to original project/product/repo/model/paper/funding/customer evidence and a true recent event date before A/B project consideration.

## Raw Search

For broad runs, create the four A/B/C/D lane result files. Do not spawn subagents for front-stage search. Main Codex first creates the Exa Candidate Queue. After that, Main Codex may process lanes sequentially, or use optional subagents only for large scans where parallel filtering/enrichment of provided Exa candidates is worth the context overhead. Optional subagent policy: model `gpt-5.4-mini`, reasoning `medium`, one result file per candidate processor.

Default lane path:

1. Main Codex runs broad Exa-only recall for the lane using the lane's keyword groups, source intent, date window, and any `Elsewhere Keyword Intelligence` terms written in `topics.md`, while keeping returned payloads in candidate-queue mode. Use `web_search_advanced_exa` with `enableSummary: false`, no subpages, `highlightsMaxCharacters` capped to a short routing snippet, and `textMaxCharacters: 1`; do not request or accept full page bodies during broad recall. Append every Exa-returned candidate URL/result to `{WORKSPACE}/exa-candidates.jsonl` before filtering, dedupe, enrichment, or context-mode compression. Persist query phrase, lane, URL, normalized URL/domain, returned title/source type hint, Exa returned/published/crawl dates when present, short highlight/routing reason, why it might matter, returned rank/batch id, collection date, lightweight triage fields, `selected_for_review=false`, `fetch_status=pending`, and empty keep/drop fields. Also write a compact lane queue view for human inspection.
2. Immediately after each lane recall batch, Main Codex updates `{WORKSPACE}/exa-candidates.jsonl` and then writes the lane's `Exa Candidate Queue` block before doing any candidate filtering or enrichment. The lane queue may be a compact review view, but the JSONL file must preserve every Exa-returned URL. Before selecting rows to open, run full lightweight triage over all rows: infer source family, entry type, possible signal, risk reason, and project/person/repo cluster; then set `must_open_reason` and `review_decision`. Triage outputs are routing hypotheses only. They must be named and treated as hypotheses (`candidate_name_hypothesis`, `possible_signal`, `risk_reason`) and must not populate final writing fields. When a row is selected, opened, kept, validated, or rated, update `selected_for_review`, `fetch_status`, `keep_drop_status`, `keep_drop_reason`, and `candidate_id` if known. Only opened/fetched rows may receive `keep_drop_status=dropped`.
3. If context-mode is available, Main Codex immediately indexes `{WORKSPACE}/exa-candidates.jsonl` plus that lane's freshly written candidate queue with `ctx_index` using a source label like `ai-mapper-{date}-{lane}-candidate-queue`. For large or high-potential URL sets, use `ctx_fetch_and_index` or `ctx_execute` extraction on Exa-returned URLs before reading long pages into conversation context. This is mandatory for broad runs unless context-mode itself is unavailable; do not wait until raw files are merged at the end. Context-mode may compact snippets and page text, but it must not shrink or rewrite the full Exa candidate audit trail. If context-mode fetching/extraction is unavailable or broken, do not attempt to replace it by bulk `web_fetch_exa` calls into chat; either repair context-mode first or mark the run partial with a `Context-Mode Unavailable` limitation.
4. Main Codex uses `ctx_search` / `ctx_execute` over the indexed queue or fetched pages to support triage and evidence routing. These snippets are routing aids only; Exa text and context-mode snippets are not source evidence.
5. Open/fetch by mandatory buckets, not by vague high-potential feel. Set `must_open_reason` to one of: `official_source`, `funding_source`, `investor_or_vc_source`, `repo_or_model_source`, `paper_or_project_source`, `query_top_result`, `source_family_coverage`, `cluster_representative`, `long_tail_audit`, or `none`. Rows with any non-`none` reason must be selected and opened/fetched unless blocked; rows with `none` remain `not_selected`/`unreviewed`, never `dropped`.
6. Use adaptive continuation after mandatory buckets: for each lane/source-family/query bucket, open another small batch only when the previous batch produced new P0/P1 candidates, new entity clusters, stronger original evidence, or financing/team/date proof. Stop a bucket only after recording low marginal yield, duplicate/stale/out-of-scope patterns, and remaining `not_selected` count.
7. Main Codex or a candidate processor opens/fetches the assigned Exa candidates and discards Exa-only noise before creating raw leads. Verification fetches must be bounded: prefer context-mode indexed fetch/extraction; if using `web_fetch_exa`, cap `maxCharacters`, batch only a few mandatory-bucket/high-yield URLs, and extract structured facts instead of reading or pasting article bodies. The original openable public page, repo, paper, model, product page, or credible report is the evidence.
8. For each kept candidate, create evidence-backed verification fields before raw/final writing: `verified_entity_name`, `verified_event_type`, `claim_supported`, `source_page_date`, `true_event_date` or explicit `date_decision`, `openable_original_url`, and `confidence_level`. If a field is only known from Exa title/snippet or lightweight triage, keep it as a hypothesis in raw/validated notes and do not write it as a final fact.
9. For each kept candidate, produce a detailed raw case: `谁在做 -> 做了什么 -> 最近动作 -> 真实事件日期 -> 背景 -> 触达路径 -> 问什么 -> 缺什么证据`.
10. Drop closed-source candidates outside Elsewhere unless equivalent public or attributed Elsewhere API evidence can support the raw lead.

Common lane-processing instruction:

```text
读取 {WORKSPACE}/topics.md 和已生成的 Exa Candidate Queue。只写指定 lane 的 result file。
不要做独立搜索或新增候选来源。只处理 Main Codex 提供的 Exa query / 候选 URL / 初筛理由，再打开/抓取原始页面筛选。Exa 摘要、Exa publishedDate/crawl date 和 context-mode 检索片段都不能直接写成事实、真实事件日期或评级证据；必须回到原始公开页面。
必须使用当前 web/source inspection，不凭记忆编项目、日期、融资、创始人或联系方式。
每条 raw lead 必须在“最近动态”或“备注”里拆分记录：source_page_date、true_event_date、exa_returned_date（如有）、collection_date、date_decision。不能用 Exa 日期替代真实事件日期。
遇到账号、私域 App、私有浏览器会话、QR 或 CAPTCHA 依赖时，不作为证据；寻找等价公开来源，找不到则降级或丢弃，并在限制中记录。
每条线索包含：名称、入口类型、类型、赛道、找谁、为什么找、怎么找、找了之后问什么、最近动态、主证据链接、补充证据链接、联系入口、证据等级、备注。
备注写：背景：{学校/前公司/项目/成绩/未确认}; 触达：{入口/未确认}; 日期：{source_page_date/true_event_date/exa_returned_date/date_decision}; 已查：{GitHub/公开 X/官网/contact/活动页/论文页/引用页...}。
禁止招聘/岗位页面。
```

Lane coverage:

- `A-dev`: GitHub/GitHub Trending/GitHub releases, Hugging Face Trending/models/spaces/datasets, Product Hunt launches, ModelScope/Gitee public project pages only when directly openable and tied to a concrete project, public hackathons/developer challenges.
- `B-content`: official/company/founder/product blogs, public launch pages, public founder/product retrospectives, demo-day recaps, accelerator interviews, and public synchronized article pages. Do not use generic community/comment feeds except Product Hunt/GitHub/Hugging Face pages from the explicit allowlist.
- `C-funding`: 36氪, 投资界, 创业邦, 猎云网, 亿欧, 雷峰网, 新智元, 量子位, 机器之心, InfoQ, DoNews, TechNode, KrASIA, company announcements, investor/VC portfolio/newsroom pages, public synchronized article pages, incubators, accelerators, demo days, roadshows. Company homepages are verification/enrichment sources when they verify project signal, product status, current action, funding/customer claims, or optional named people/contact details.
- `D-academic`: arXiv, OpenReview, Semantic Scholar, OpenAlex, Papers With Code, ACL Anthology, CVF, NeurIPS/ICLR/ICML proceedings, project/repo/demo pages linked from papers, public lab pages. Citation/venue/repo/demo signals feed project rows and `关联人才与背景`; do not create a separate academic talent table.

Minimum per lane: follow `references/run-modes.md`. Default standard scan uses adaptive lane targets (`A-dev` 10-14 queries, `B-content` 8-12, `C-funding` 14-22, `D-academic` 8-12) with C-funding as the highest-weight lane. Deep map uses the higher lane targets in `references/run-modes.md`. Preserve candidate breadth with enough `numResults`; keep all plausible P0/P1 raw leads through validation. If a lane falls below the selected mode's query/candidate/opened/raw/source-family minimum, write the exact source exhaustion or access blocker in `run-report.md` and mark the run partial/degraded as appropriate. Context compression must not be used as a reason to search less. A lane may be processed by Main Codex or an optional subagent after the Exa Candidate Queue exists, but the output schema is identical and no non-Exa candidate sources may be added by processors. The opened/fetched set must include all mandatory buckets plus adaptive continuation, not only rows that look high-potential from Exa title/snippet.

Each lane result file must include an `Exa Candidate Queue` block before the raw table:

```markdown
## Exa Candidate Queue
| Exa query | Candidate URL | Why it might matter | Opened/fetched? | Keep/drop reason |
|---|---|---|---|---|
```

Raw result table:

```markdown
| 名称 | 入口类型 | 类型 | 一句话描述 | 赛道 | 找谁 | 为什么找 | 怎么找 | 找了之后问什么 | 最近动态 | 主证据链接 | 补充证据链接 | 联系入口 | 证据等级 | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
```

For a raw example row, read `references/examples.md#raw-lead-example`. Do not copy example names as real leads.

Coverage block must include: 搜索次数, 有效线索, 入口类型分布, 找到背后的人/团队, 找到联系方式或触达入口. Evidence levels: `S` original/GitHub/author/product/contact page; `A` founder interview/team/verified/direct profile/Elsewhere first-hand reporting with attribution; `B` media/event/podcast/report/Elsewhere analysis or mention; `C` weak but checkable; `无效`. Elsewhere keyword intelligence alone is not evidence.
