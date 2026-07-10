# AI Mapper Elsewhere Policy

Read this before using the Elsewhere API for keyword intelligence, project discovery, financing pass, or enrichment.

## Table of Contents

- [Elsewhere Preflight And Keyword Intelligence](#elsewhere-preflight-and-keyword-intelligence)
- [Elsewhere API Data Source](#elsewhere-api-data-source)
- [Elsewhere Financing Pass](#elsewhere-financing-pass)
- [Output Integration](#output-integration)

## Elsewhere Preflight And Keyword Intelligence

Before Exa recall, resolve Elsewhere API connection status with a lightweight preflight. If Elsewhere is available, run Elsewhere keyword intelligence plus project discovery. If no key is configured/provided or the API returns quota/rate exhaustion, write an `Elsewhere unavailable` block into `topic.md`, `topics.md`, final report/latest pointer, and `run-report.md`; then continue broad Exa recall as `degraded / Exa-only` using baseline query groups and mark only the missing Elsewhere source layer as `待补 Elsewhere`. Team/person/background/contact gaps still require public-web/Codex search wording. For keyword intelligence, refresh frontier industry vocabulary, founder/company phrasing, product categories, investor language, recent financing terms, and emerging topic names related to the generic scan and any user-emphasized direction. Write a compact `Elsewhere Keyword Intelligence` block into `topics.md`:

```markdown
## Elsewhere Keyword Intelligence
| Seed/topic | Elsewhere query | Frontier terms | Founder/company phrases | Exa query angles | Evidence note |
|---|---|---|---|---|---|
```

Use this block to improve Exa query phrasing, synonyms, and source-intent coverage. Do not treat Elsewhere keyword hits alone as candidate evidence.

For Elsewhere project discovery, run targeted Elsewhere queries for source-backed reporting on relevant companies, products, founders, funding, and ecosystem themes. Extract project/company/person names from every relevant Elsewhere chunk/article instead of using the article only as vocabulary. Keep these candidates separate from A/B/C/D lane files and record them as an `Elsewhere API discovery/supplement` pool with query, endpoint, title/author/date, URL, extracted project/person facts, verification status, and next source to verify. Elsewhere-discovered projects can enter `validated.md`, `rated.md`, and final tables when the reporting is substantive and linkable, subject to the rating caps below. Use the selected run mode's Elsewhere budget from `references/run-modes.md`: default standard scan minimum/target/cap is `5 / 8-15 / 20` Elsewhere financing/startup candidate facts; deep map minimum is `20`. If Elsewhere is available but returns fewer direct candidates, explicitly state which queries produced no project candidates and diagnose the cause. The final report or run report must name which Elsewhere candidates entered A/B/C and which were downgraded, so Elsewhere discovery is visible instead of hidden in notes.

## Elsewhere API Data Source

Elsewhere is a first-hand reporting corpus for China's tech and venture ecosystem. It is not an Exa tool and not a lane processor tool. Main Codex operates it directly as a mandatory project-discovery, evidence, and enrichment source for every complete run. If it is unavailable because the key is missing or quota/rate limits are exhausted, the run may continue only as `degraded / Exa-only` with standard output paths and explicit status labels. Read `references/source-policy.md` for the binding source rules.

Mandatory Elsewhere pass:

- Resolve the key before discovery: `KEY="${ELSEWHERE_KEY:-$(cat ~/.config/elsewhere/key 2>/dev/null)}"`.
- If no `els_live_...` key is found, or the API returns quota/rate exhaustion such as `429 quota_exceeded`, write the Elsewhere unavailable/degraded block from `references/blockers.md`, continue with Exa + open public sources when Exa is available, and mark the run `degraded / Exa-only`; do not mark it `complete`.
- Run keyword intelligence before Exa query drafting.
- Run project discovery before validation and keep it in `Elsewhere API discovery/supplement`.
- Run the `Elsewhere Financing Pass` before C-funding rating. Elsewhere is not allowed to be only keyword/context in a normal run.
- Run enrichment checks for likely A/B projects and all named people before final rating.
- Do not use Elsewhere as a substitute for opening original project/repo/product/funding pages when those pages are needed for the row type.

Operation rules:

1. Read the Elsewhere API reference before first endpoint use in a session and use exact field names.
2. For keyword intelligence and project discovery, prefer `GET /search/chunks?q=&k=&published_after=&recency=prefer`, `GET /topics?q=&limit=`, and `GET /relation-keys?category=` when useful. For entity/fact enrichment, prefer `GET /entities/find?name=`, `GET /entities/search?q=&k=`, `GET /entities/{id}/card`, `GET /entities/{id}/edges`, and `GET /content/{type}/{id}?lang=zh`.
3. Attribute every substantive Elsewhere-derived claim as `Elsewhere · {author/title/date}` with link. For `search/chunks`, build links as `https://elsewhere.news/zh/{author_slug}/{slug}`; never invent slugs.
4. Never paste full articles. Use concise facts, context, numbers, relationships, and uncertainty.
5. Keep Elsewhere facts separate from Exa/open-web facts in notes. If they conflict, record the contradiction and do not silently merge.
6. Elsewhere-discovered names may be new project/person candidates, not only enrichment for existing rows. If Elsewhere surfaces a source-backed project/person, Main Codex may add it as an `Elsewhere API discovery/supplement` candidate in validated/rated, with `来源平台=Elsewhere API`, `source_origin=Elsewhere API`, API query/endpoint, and explicit attribution. Do not put Elsewhere-only discoveries into lane result files as if they came from Exa.
7. Elsewhere-only candidates can enter the output table when the reporting itself is substantive and linkable, but they cannot be rated A unless project signal, freshness, why-now, and at least one original/open project/product/repo/company/funding source are also verified or clearly not needed for that row type. Otherwise keep B / 待补原始项目证据 or C / 背景样本.

## Elsewhere Financing Pass

Run this pass after keyword intelligence and before `validated.md` when Elsewhere is available. If Elsewhere is unavailable because the key is missing or quota/rate limits are exhausted, skip these API calls, record the exact unavailable reason, set Elsewhere financing/startup candidate facts to `0 / degraded`, and write `待补 Elsewhere Financing Pass` only where this missing source affects Elsewhere-derived financing/startup context:

1. Use the active date windows. Query with `published_after` for the priority window and again for the observation window when needed. Prefer `recency=filter` for strict date windows and `recency=prefer` for broader semantic expansion.
2. Use financing-event queries, not only product-category queries. Include combinations of `融资`, `完成融资`, `天使轮`, `种子轮`, `Pre-A`, `早期项目`, `一级市场`, `投资方`, `创始人`, plus AI software categories such as `AI Agent`, `AI office`, `Coding Agent`, `MCP`, `AI infra`, `模型路由`, `企业数据`, `workflow automation`.
3. Use `/search/chunks` with high enough `k` to inspect article clusters, not just top snippets. For candidate-rich content, fetch `/content/{type}/{id}?lang=zh` and extract every mentioned company/project/person/funding/investor fact.
4. Use `/me/whats-new?since=<priority_window_start>&lang=zh` when connected, then inspect funding- and startup-related items even if they were not returned by semantic search.
5. Use `/topics?q=融资 AI&limit=...`, `/topics?q=一级市场 AI&limit=...`, and topic detail endpoints when useful to find article clusters. Use entity search/cards/edges when a candidate company/person is found and the schema exposes financing, investment, founder, or portfolio relationships.
6. Each extracted candidate fact must include: project/company, person if present, financing/event phrase, investor if present, article/content title, author, published date, Elsewhere URL, and next original source to verify.
7. Follow the selected mode's Elsewhere financing/startup fact budget from `references/run-modes.md`: standard scan `5 / 8-15 / 20`, deep map minimum `20`. If Elsewhere returns zero direct candidates, mark the Elsewhere section partial and diagnose whether the cause is query design, endpoint coverage, date filter, API/key issue, or true coverage gap.

## Output Integration

- In `topics.md`, add `Elsewhere Keyword Intelligence` when used. Preserve Elsewhere query, extracted terms, founder/company phrases, and how they changed Exa query angles.
- In `validated.md`, add an `Elsewhere API discovery/supplement` subsection when Elsewhere is used for project discovery or new candidate sourcing. Preserve query/endpoint, title/author/date, URL, extracted candidate facts, original-source verification status, and whether the fact came from the `Elsewhere Financing Pass`.
- In the final report or `run-report.md`, add an Elsewhere discovery summary by candidate name: `entered A/B`, `entered C/background`, `downgraded`, or `not used`, with the reason. Elsewhere-sourced projects must be visible even when they are not promoted.
- In `项目背景与证据`, add Elsewhere facts only when they explain the project, product status, founder logic, funding, market context, or recent action.
- In `关联人才与背景`, prefer public-web/Codex search sources for founder/team background and person-project relationship. Elsewhere facts may be cited only when source-backed and linkable; they must not be the required follow-up path for unresolved team/person fields.
- In `来源链接`, include the Elsewhere article/content URL when Elsewhere materially supports a project row. In `项目背景与证据` or talent `背景`, label the fact as `Elsewhere API · {author/title/date}`.
- In `下一步补全项`, do not use Elsewhere backfill or coverage wording for Team, Person, Background, Contact, Product proof, Customer/user proof, Evidence, or Date verification. Use the exact public-web/Codex search gap instead.
- In 来源质量复盘, add a row for `Elsewhere API`: `用途 | query count | keyword terms/chunks/entities/content used | entered A/B | gaps/limitations`.
