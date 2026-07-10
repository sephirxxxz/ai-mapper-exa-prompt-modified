# AI Mapper Rating Rubric

Read this before writing `validated.md`, `rated.md`, or the final report.

## Table of Contents

- [Project-First Rule](#project-first-rule)
- [Recency And Date Gate](#recency-and-date-gate)
- [Academic Project Integration](#academic-project-integration)
- [Ratings](#ratings)
- [Gap Enum](#gap-enum)
- [Talent Rows](#talent-rows)
- [Downgrade Rules](#downgrade-rules)
- [Output Quality Pass](#output-quality-pass)

## Project-First Rule

A strong project can be A even when person, background, or contact is unresolved. These are enrichment fields, not project-level hard gates.

However, unresolved enrichment is not permission to skip enrichment. Before any A/B rating, public-web checks for people, team, background, funding, and product proof must be attempted and documented. Elsewhere availability is a run-status/source-layer note; it does not satisfy Background, Funding, Evidence, Customer/user proof, Person-project relation, or Date verification gaps.

## Recency And Date Gate

For normal `TOPIC=通用扫描`, "new" means true event date, not search-engine freshness.

| Window | Treatment |
|---|---|
| 0-30 days from run date | Priority pool for A/B market/startup/funding leads |
| 31-60 days from run date | Observation pool; normally B only when evidence and why-now are strong |
| Older than 60 days | C/background unless a new openable event inside the priority window reactivates the project |

Every A/B candidate must record `source_page_date`, `true_event_date`, `exa_returned_date` if present, `collection_date`, and `date_decision`. Exa `publishedDate`, crawl date, snippets, summaries, or rank order are not freshness evidence.

Required A project gates:

| Gate | A requirement |
|---|---|
| Scope | Chinese/China-relevant AI software under `TOPIC=通用扫描` |
| Early | Not mature, big-company, B-round-or-later, or high-financing |
| Project signal | Clear product/repo/company/program/paper-system with a concrete AI software direction |
| Freshness | Market/startup/funding leads have a true event date inside the 0-30 day priority window. Academic project leads have a recent paper/repo/model/demo event or a current productization/funding signal. |
| Evidence | Product/demo/GitHub/Hugging Face/research paper/repo/funding/user/customer/repeated output |
| Why now | Concrete reason for 李曼 to care now, not market heat |

A-class evidence floor: if the row depends on a single media/report page and public enrichment does not verify at least one stronger original source family (product/company site, GitHub/release, repo/model/demo, customer/deployment proof, investor/VC page, company announcement, founder/team page, or public profile), cap it at B even when Scope, Early, Project signal, Freshness, and Why now look promising.

Enrichment status:

| Field | Treatment |
|---|---|
| Person/team | Optional for project A. If missing, write `待补负责人/核心团队` plus what was checked. |
| Background | Optional for project A. If missing, write `待补团队背景` plus the next detailed-search path. |
| Contact | Optional for project A. If missing, write `待补触达路径`; generic company contact is weak project contact only. |

## Academic Project Integration

Do not create a separate academic talent table. Academic evidence enters the existing project workflow when there is a projectized artifact:

- paper/system/benchmark/repo/demo/model/dataset/product/lab spinout;
- strong signal from top venue, citation/usage, benchmark adoption, public repo/demo, Hugging Face/Papers With Code activity, or recent commercialization/funding;
- clear path from artifact to application potential inside AI software.

Put paper title, venue, citation/source, repo/demo/model links, author/lab background, and commercialization/funding context into `项目背景与证据` and `关联人才与背景`. A person enters the existing talent table only when their person-project relation, recent action, and public profile/background evidence are sufficient.

## Ratings

| Rating | Use when |
|---|---|
| A / 重点关注 | Project gates pass and row has enough evidence, true recency, and why-now for immediate mentor judgment |
| B / 继续观察 | Direction is relevant but one of Background, Contact, Freshness, Funding, Evidence, Why now, Project signal, Customer/user proof, or Person-project relation needs concrete follow-up |
| C / 轻量记录 | Useful ecosystem/background signal, but mature, big-company/lab, stale, broad, older than the active window, or weakly aligned |
| 暂不跟进 | Public evidence insufficient, closed-source-only, database/community-only, recruitment-only, out of scope, or unverifiable |

## Gap Enum

Use these exact gap values in `下一步补全项`, `rating`, `candidates.jsonl.gap_type`, and downgrade notes. Do not write generic gaps such as `继续关注`, `待观察`, or `后续跟进` without one of these values.

| Gap | Use when |
|---|---|
| `Background` | Team/person background is missing or weak |
| `Contact` | Public personal/project contact path is missing or weak |
| `Freshness` | True event date is outside the active window or unclear |
| `Funding` | Financing round/date/investor evidence is missing or contradictory |
| `Evidence` | Original/openable source does not support the claim strongly enough |
| `Why now` | Relevance to 李曼 is generic market heat rather than a concrete current reason |
| `Project signal` | Product/repo/company/paper-system is not concrete enough |
| `Customer/user proof` | Usage/customer/deployment proof is missing for a business-facing claim |
| `Person-project relation` | Named person is not clearly tied to the project/work |
| `Date verification` | Source page date, true event date, or date decision is unresolved |
| `Elsewhere` | Elsewhere source layer for keyword/discovery/financing/startup context is unavailable or incomplete; do not use this for team/person/background/contact gaps |
| `Public evidence` | Candidate depends on closed/account-only/private evidence |

## Talent Rows

Final talent rows intentionally use the compact talent-table schema in `references/schemas.md`:

```markdown
| 姓名/昵称 | 关联公司/项目 | 最近动作 | 身份 | 背景 | 评级 |
|---|---|---|---|---|---|
```

Do not replace it with a full-width talent table, scholar list, or academic-only table.

Talent A requires:

- Named person/team.
- Clear person -> company/project/work relation.
- `最近动作` is source-backed, preferably within the last 30 days for normal scans, and names the absolute true event date plus action type such as financing, product launch, beta, open-source growth, demo day, roadshow, interview, paper/repo/model release, or customer/deployment proof when available.
- `背景` is source-backed through education, prior company, representative project, open-source/paper/product proof, funding/team fact, or public profile. Fold source type, source URL label, and contact gap into this cell when useful.
- `评级` states A/B/C plus the most important reason or missing field. Missing direct contact alone cannot block a source-backed talent row.

Stale founders/maintainers without recent action stay as project enrichment or C/background, not A/B talent. A project with unresolved person/contact can enter project A, but must not be forced into the talent table.

## Downgrade Rules

| Situation | Rating action |
|---|---|
| Early repo/product + true event inside 30 days + original evidence + clear 李曼 project question | A project row; mark unresolved person/contact/background as `待补` |
| Early repo/product + named maintainer + current activity + public profile/background evidence + clear 李曼 question | A project row and possible A talent row |
| Product/funding evidence but responsible person or contact path is weak | A project row if project gates pass; otherwise B with exact missing field |
| Single media/report source + unresolved team/funding/product proof after public enrichment | Cap at B with Background, Funding, Evidence, or Customer/user proof gap |
| Elsewhere is used as the next step for team/person/background/funding/product proof | Rewrite as a public-web/Codex search gap and cap at B until public enrichment is attempted |
| Funding/article/project page is 31-60 days old | Normally B/继续观察 if strong; otherwise C/background |
| Funding/article/project page is older than 60 days and no new event exists | C/background or 暂不跟进 |
| Mature company, big-company product, B-round-or-later, high financing, or stale activity | C/background unless explicitly requested |
| Product Hunt/GitHub/Hugging Face radar appearance only | Raw/validated lead at most; backtrace before A/B |
| Broad ranking database, generic AI tool directory, or generic community heat | Drop or background; do not use as A/B evidence |
| Academic paper/person with no projectized artifact or application path | C/background; do not create academic talent row |
| Generic `contact@`, sales form, HR path, or company homepage only | Weak project contact only; cannot make a talent A, and missing direct contact alone cannot block a source-backed talent row |
| Elsewhere-only candidate without original project/product/repo/company/funding verification | Cap at B unless it is explicitly a background/context row |

## Output Quality Pass

Before final delivery:

1. Re-audit every A project row against Scope, Early, Project signal, Freshness, Evidence, Why now, and Date decision.
2. Record Public-Web Enrichment status for Team, Funding, Product proof, and Date proof; list checked public source families when unresolved.
3. Record Person, Background, and Contact as `resolved / partial / 待补`.
4. Expand every A/B project row into the high-density table from `references/schemas.md`.
5. Replace generic filler such as `未确认`, `待补`, `官网`, `contact@`, `可关注`, Elsewhere status wording in row-level gaps, or market heat with evidence or a concrete public-web/Codex search gap.
6. Downgrade rows whose evidence, project signal, true freshness, early status, why-now, or public enrichment basis is weak.
