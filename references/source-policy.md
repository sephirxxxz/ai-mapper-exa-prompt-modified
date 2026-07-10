# AI Mapper Source Policy

Read this before every ai-mapper run.

## Table of Contents

- [Binding Rules](#binding-rules)
- [Open Public Source Allowlist](#open-public-source-allowlist)
- [Public-Web Enrichment](#public-web-enrichment)
- [Mandatory Elsewhere Pass](#mandatory-elsewhere-pass)
- [Elsewhere Attribution](#elsewhere-attribution)
- [Evidence Classes](#evidence-classes)
- [Public Source Boundary](#public-source-boundary)
- [Banned Sources](#banned-sources)
- [Weak Signals](#weak-signals)

## Binding Rules

- Elsewhere API is mandatory for every complete run. If it is unavailable because no key is configured or quota/rate limits are exhausted, continue only as `degraded / Exa-only` with standard output paths and explicit status labels; do not call the run complete.
- Exa is mandatory for front-stage A/B/C/D lane recall.
- Context-mode is a context-hygiene tool only. It is never evidence.
- Use only public, openable original sources plus attributed Elsewhere API.
- Elsewhere is mandatory for complete runs, but public-web enrichment is mandatory for all likely A/B candidates in complete and `degraded / Exa-only` runs. Do not let `待补 Elsewhere` stand in for open public searches that can verify team, person, background, contact, funding, product proof, customer/user proof, repo/model/demo evidence, or true event dates.
- Recency must be judged by true event date and source page date, not Exa crawl date, Exa `publishedDate`, search rank, snippets, or summaries.
- Broad ranking databases, generic AI tool directories, generic community feeds, login/paywall/account-only databases, and closed communities are out of scope.
- Keep only the explicit public community/product radar allowlist: Product Hunt, GitHub/GitHub Trending/GitHub releases, Hugging Face Trending/models/spaces/datasets, plus directly openable original project/repo/product/paper/funding pages.
- Do not use account-only, private browser state, QR-code, CAPTCHA, paywall, or closed app sources.
- Do not use recruitment/job-board paths as discovery, evidence, contact, or rating signals.
- Do not create a separate academic talent table. Academic papers, citation signals, and top-conference evidence enter existing project rows when they are tied to a projectized artifact; people enter the existing talent table only if they independently qualify.

## Open Public Source Allowlist

Use these sources only when directly openable and traceable:

- Original project evidence: product site, company site, GitHub repo/release, Hugging Face model/space/dataset, paper page, demo page, docs, customer/deployment page.
- Funding and venture evidence: 36氪, 投资界, 创业邦, 猎云网, 亿欧, 雷峰网, 新智元, 量子位, 机器之心, InfoQ, DoNews, TechNode, KrASIA, company announcements, investor/VC portfolio pages, VC newsroom pages, and public synchronized article pages.
- Public community/product radar exceptions: Product Hunt launches, GitHub/GitHub Trending/GitHub releases, Hugging Face Trending/models/spaces/datasets.
- Academic evidence: arXiv, OpenReview, Semantic Scholar, OpenAlex, Papers With Code, ACL Anthology, CVF, NeurIPS/ICLR/ICML proceedings, public lab/project pages, and linked repo/demo/model pages.

Use radar sources to discover names and timing hypotheses, then backtrace to original evidence. Do not cite a ranking/community surface as the primary reason a row is A/B.

For normal runs, source breadth follows the selected mode in `references/run-modes.md`; count families using `references/source-families.md`. Default `adaptive standard scan` requires at least 10 distinct open source families and at least 6 C-funding source families; `deep map` requires at least 18 and 10. If a source family is queried but yields no openable result, record `queried/no usable result` in the run report. Do not replace source breadth with a small number of generic Exa queries.

## Public-Web Enrichment

After candidate discovery and before rating, run targeted public enrichment for likely A/B rows and all named people. This pass is required even when Elsewhere is unavailable and still required when Elsewhere is available.

For each likely A/B project, try to verify:

| Field | Open public sources to check |
|---|---|
| Team | company/product About or Team page, founder interview, GitHub org/maintainer, paper author/lab page, public personal site, public X/GitHub profile |
| Funding | 36氪, 投资界, 创业邦, 猎云网, 亿欧, 雷峰网, InfoQ, DoNews, TechNode, KrASIA, company announcement, investor/VC portfolio/newsroom |
| Product proof | product/company site, docs, demo, GitHub release, Hugging Face/ModelScope page, paper project page, customer/deployment page |
| Date proof | original article/page date, financing announcement date, release/tag/model upload date, paper v1 date, customer/deployment date |

If a field cannot be resolved after public enrichment, record the checked source families and the exact gap enum. `待补 Elsewhere` may be added only for the missing Elsewhere source layer in status/source-quality notes; it must not appear as the next step for Team, Person, Background, Contact, Funding, Product proof, Customer/user proof, Evidence, or Date verification.

## Mandatory Elsewhere Pass

Resolve the key before discovery:

```bash
KEY="${ELSEWHERE_KEY:-$(cat ~/.config/elsewhere/key 2>/dev/null)}"
```

Run a lightweight availability preflight before broad discovery. If no `els_live_...` key is found, or the API returns quota/rate exhaustion such as `429 quota_exceeded`, write the Elsewhere unavailable/degraded block from `references/blockers.md`, continue with Exa + open public sources when Exa is available, and mark the run `degraded / Exa-only`. Use the standard final/raw/latest paths; do not create alternate `*-exa-only` filenames; do not call the run complete.

When Elsewhere is available, use it in three places:

1. Keyword intelligence before Exa query drafting.
2. Project/person discovery before `validated.md`.
3. Attributed source/context checks for likely A/B projects before final rating; team/person/background still require public-web/Codex search.

Keep Elsewhere candidates in `Elsewhere API discovery/supplement`. Do not insert them into A/B/C/D lane files as if Exa found them. Final or run-report output must name Elsewhere candidates and their disposition: entered A/B, entered C/background, downgraded, or not used.

Elsewhere must be used as an explicit financing/startup candidate source, not only as vocabulary, when available. A complete run runs an Elsewhere Financing Pass using date-windowed `/search/chunks`, `/me/whats-new`, topics, and content fetches where useful. Extract company/project/person/funding/investor facts from returned articles. If no direct candidates are found, record query/endpoint attempts and diagnose query design, endpoint coverage, date filter, API/key issue, or true corpus gap. In `degraded / Exa-only` runs, record `Elsewhere Financing Pass: not run - unavailable`, set extracted facts to `0 / degraded`, and mark only the Elsewhere source layer `待补 Elsewhere`.

Elsewhere source checks complement public-web enrichment; they do not replace it. If Elsewhere is unavailable, continue public-web Team/Person/Background/Funding/Product proof enrichment and distinguish public-source gaps from the unavailable Elsewhere source layer.

## Elsewhere Attribution

Attribute every substantive Elsewhere-derived claim as:

```text
Elsewhere · {author/title/date}
```

Include the Elsewhere URL in `来源链接` whenever it materially supports a row. For `search/chunks`, build links from returned `author_slug` and `slug`; never invent slugs.

Elsewhere keyword intelligence alone is not evidence. Elsewhere article/content/entity facts can support background, funding, person-project relationships, and market context when source-backed and linkable.

Elsewhere-only candidates can enter output tables only when reporting is substantive and linkable. They cannot be rated A unless project signal, freshness, why-now, true event date, and at least one original/open project/product/repo/company/funding source are verified or clearly not needed for that row type.

## Evidence Classes

| Level | Meaning |
|---|---|
| S | Original product/repo/author/contact page, GitHub, Hugging Face, paper, product docs, customer/demo/funding source |
| A | Founder interview, verified team/profile, direct public profile, Elsewhere first-hand reporting with attribution |
| B | Media/event/podcast/report/Elsewhere analysis or mention |
| C | Weak but checkable public source |
| 无效 | Closed, unverifiable, repost-only, recruitment-only, stale, crawl-date-only, or unrelated |

Rated rows need at least one openable, traceable, non-repost evidence link. Exa snippets, Exa summaries, Exa returned dates, context-mode snippets, ranking snippets, and community heat are routing aids only.

## Public Source Boundary

Closed platforms are out of scope for search, enrichment, evidence, and rating, except mandatory Elsewhere API through the user's configured/provided key. A project lead can survive when public sources or attributed Elsewhere API reporting are enough to verify the project/product/repo, current activity, and evidence. Responsible person/team and background are enrichment fields for project leads and required for talent rows; contact path is optional context only and never a final talent-column.

When a promising candidate points to a closed source:

1. Try to find equivalent public or attributed Elsewhere API evidence from product, repo, author, event, media, paper, investor pages, or Elsewhere article/entity/content endpoints.
2. If equivalent evidence exists, use that evidence and cite the source type clearly.
3. If no public evidence exists, drop the candidate or keep it as `暂不跟进 / 公开证据不足`.
4. Record the limitation in `run-report.md`; do not create a follow-up queue that depends on private user session state.

Tag every raw lead:

| Entry type | Resolution |
|---|---|
| `person` | person -> project/work -> background -> contact |
| `project` | project -> founder/author/maintainer/team -> background -> contact |
| `repo` | repo -> owner/contributors/maintainer -> product/use case -> contact |
| `content` | content -> mentioned person/project -> original evidence -> contact |
| `event` | event -> participating project/team/person -> post-event activity -> contact |
| `paper` | paper -> authors/lab/repo -> application potential -> contact |

Target normalized object: `项目/产品/Repo -> 做了什么 -> 最近动作 -> 项目信号 -> 负责人/团队(可待补) -> 背景(可待补) -> 触达路径(可待补) -> 是否值得跟进`.

## Banned Sources

Do not use these as discovery, evidence, contact paths, or rating signals:

- Boss直聘
- 拉勾
- 猎聘
- 脉脉招聘
- Hiring pages, job posts, hiring posters
- Private WeChat groups, QR-only pages, private app sessions
- Pages behind login, CAPTCHA, account-only access, or paywalls
- Generic AI tool directories and broad ranking databases as discovery/rating sources, including AI产品榜/AICPB, 华军AI产品榜, 猫目, Futurepedia, and similar directories
- Generic community/comment feeds as discovery/rating sources, including V2EX, 掘金, 开源中国, 观猹/watcha.cn, 小宇宙, and similar feeds, except for the explicit allowlist of Product Hunt, GitHub, and Hugging Face
- Company/funding databases that require login/paywall or behave as broad database lookups, including IT桔子, 烯牛数据, 企名片, 天眼查, 企查查, PitchBook, Crunchbase, and similar services

If a promising candidate appears only in a closed source, broad database, or generic community/ranking source, try product/repo/company/event/media/investor/academic pages and Elsewhere when available. In `degraded / Exa-only` runs, do not use closed sources as a substitute for Elsewhere; downgrade to `暂不跟进 / 公开证据不足` or mark `待补 Elsewhere` only when open public evidence already supports keeping the project.

## Weak Signals

These may support context but cannot by themselves make an A/B row:

- Product Hunt/GitHub/Hugging Face trending appearance without original evidence
- Ranking/index appearance
- Community ratings, comments, or heat
- Exa rank order, highlights, summaries, or returned dates
- Generic `contact@`, support, PR, sales, HR, or company form
- Static homepage copy without recent activity
- Market-heat language such as `很热门` or `值得关注`
- Older financing/news/article pages that are only newly crawled or newly surfaced

Generic contact can remain as weak project-level contact, but it cannot make a talent A; missing direct contact alone cannot block a talent row when recent action, person-project relation, and background are source-backed.
