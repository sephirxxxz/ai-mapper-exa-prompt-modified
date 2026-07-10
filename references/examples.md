# AI Mapper Case Library

Use this file to calibrate output quality. These are historical examples, not current evidence. Do not copy names, dates, funding, activity, or contact paths into a new run without fresh source inspection.

## Table of Contents

- [How To Use](#how-to-use)
- [Current Final Project Table Shape](#current-final-project-table-shape)
- [Case Responsibility By Stage](#case-responsibility-by-stage)
- [Raw Lead Example](#raw-lead-example)
- [01 Good A Project Card: Early Coding-Agent Infrastructure](#01-good-a-project-card-early-coding-agent-infrastructure)
- [02 Good A Talent Card: Builder Behind The Project](#02-good-a-talent-card-builder-behind-the-project)
- [03 Good A Project Card: Enterprise Workflow / DataAgent](#03-good-a-project-card-enterprise-workflow-dataagent)
- [04 B Row That Should Not Be A Yet](#04-b-row-that-should-not-be-a-yet)
- [05 C / Background Sample](#05-c-background-sample)
- [06 Output Quality Audit Case](#06-output-quality-audit-case)
- [Rating And Downgrade Examples](#rating-and-downgrade-examples)
- [Common Bad Outputs](#common-bad-outputs)
- [Thin Row Red Flags](#thin-row-red-flags)
- [Early Stop Examples](#early-stop-examples)

## How To Use

- Read this when raw rows are thin, A/B ratings feel ambiguous, or the final report is becoming a radar list instead of high-density judgment tables.
- Use the cases to match reasoning depth, not to preserve the exact wording.
- Keep broad discovery in raw/validated artifacts; final A/B rows should increase judgment density inside the table cells themselves. Supplemental judgment notes are optional reinforcement for strategically important rows.
- Current project-first policy: historical A examples below may include legacy direct-contact wording and old table schemas. Use them for reasoning density only; do not copy their column order. Project-level A no longer requires resolved founder/person/contact/background. A strong project can enter `A / 重点关注` with `待补负责人/核心团队`, `待补团队背景`, or `待补触达路径` when Scope, Early, Project signal, Freshness, Evidence, and Why now are strong. Talent A still needs person/work relation and source-backed background; contact is included when public and useful.

## Current Final Project Table Shape

Use this table shape for every A/B/C project in the final report. The table is the primary judgment surface; each cell should carry enough project and person background for 李曼 to decide without opening raw files.

```markdown
| 项目名 | 一句话描述 | AI 软件细分方向 | 产品形态 | 项目背景与证据 | 融资状态 | 关联人才与背景 | 下一步补全项 | 评级 | 来源链接 | 采集日期 | 最近有效动态日期 |
|---|---|---|---|---|---|---|---|---|---|---|---|
```

Minimum density:

- `项目背景与证据`: 2-4 concrete facts about product/repo/demo/customer/funding/activity and source type.
- `关联人才与背景`: founder/maintainer/core team plus school/company/open-source/research/product facts when known.
- `下一步补全项`: exact future detailed-search gap, not a generic action or contact recommendation.

Use a compact supplemental judgment card only when the row is strategically important or still too dense after the table.

## Case Responsibility By Stage

| Stage | Good case detail | Failure mode |
|---|---|---|
| Candidate/snippet | Main Codex Exa query, URL, snippet reason, whether opened | Treating snippet as evidence or adding non-Exa candidate sources |
| Lane raw lead | Responsible person/team, current action, original evidence, background/contact gaps, one possible question | Project name + homepage only |
| Main verified case | Identity resolution, cross-lane dedupe, project-gate audit, evidence/freshness/why-now checks, enrichment status for person/contact/background | Promoting a project before original evidence, freshness, project signal, or why-now is resolved |

## Raw Lead Example

Raw lead rows are not final recommendations. They preserve traceable evidence for later validation.

```markdown
| 名称 | 入口类型 | 类型 | 一句话描述 | 赛道 | 找谁 | 为什么找 | 怎么找 | 找了之后问什么 | 最近动态 | 主证据链接 | 补充证据链接 | 联系入口 | 证据等级 | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 示例 MCP Repo | repo | 开源项目 | 面向企业知识库的 MCP server | MCP / devtools | repo owner / maintainer | 有可验证代码和近期 commit，可反查维护者 | GitHub profile -> personal site/X/GitHub issue | 是否愿意开放早期用户或介绍使用场景 | 2026-05 pushed / release | https://github.com/example/example-mcp | maintainer profile; issue thread | GitHub issue / personal site | S | 背景：owner 有前公司/开源记录待核实; 触达：GitHub issue 可用; 已查：GitHub/profile/README |
```

## 01 Good A Project Card: Early Coding-Agent Infrastructure

Historical pattern from `0524-ai-mapper.md`.

| Field | Example shape |
|---|---|
| 原始入口 | V2EX launch thread + GitHub repo |
| 归一化对象 | Mainline -> huoru / ChristopherWu |
| 为什么能进 A | Early coding-agent memory layer; named author; current release/dogfood signal; direct V2EX/GitHub contact path; clear why-now for AI software team workflow |
| 证据链 | GitHub repo for product/code; V2EX thread for launch, author, and current activity |
| 触达路径 | V2EX 私信/评论, GitHub issue/discussion, product site |
| 下一步问题 | 是否愿意给 5+ 人 AI 编程团队做深度访谈/内测 |
| 最终关系 | Author/founder relation is explicit: `huoru/ChristopherWu 是作者/发起人` |

Legacy dense-row example. Do not copy this column order; map the facts into the current final project table schema above:

```markdown
| A / 重点关注 | Mainline | Git-native memory layer for coding agents，让 agent 改代码前先读取历史意图与约束 | coding agent memory / repo context | huoru/ChristopherWu 自述 staff engineer，已 dogfood 一个月；开源 v0.1，12 个核心命令 | 未公开披露 | V2EX 私信/评论、GitHub issue/discussion、mainline.sh | 先在 V2EX/GitHub 提一个具体问题：是否愿意给 5+ 人 AI 编程团队做深度访谈/内测 | https://github.com/mainline-org/mainline | https://www.v2ex.com/t/1210451 | 2026-05-24 | 2026-05 | 解决 coding agent 高频误改、历史决策缺失问题，和李曼关心的 AI 软件团队生产方式高度相关 | huoru/ChristopherWu 是作者/发起人 |
```

Why this works: the row is not just "repo + link"; it contains project signal, person relation, evidence, freshness, and the missing/next completion field.

## 02 Good A Talent Card: Builder Behind The Project

Historical pattern from `0524-ai-mapper.md`.

| Field | Example shape |
|---|---|
| 原始入口 | Project row points to named builder profile |
| 归一化对象 | huoru / ChristopherWu |
| 为什么能进 A | Person is tied to a concrete project, current launch, and direct user-research question |
| 证据链 | V2EX member/page + launch thread + repo/product evidence |
| 触达路径 | V2EX, GitHub issue |
| 下一步问题 | 5+ 人团队使用 agent 的真实误改案例和内测要求 |
| 最终关系 | 作者/发起人 |

Legacy dense-row example. Do not copy this column order; map the facts into the current final talent table schema in `SKILL.md`:

```markdown
| A / 重点关注 | huoru / ChristopherWu | Mainline 作者，把 coding agent 的历史意图记忆放进 Git | 独立开发者/工程负责人 | coding agent memory | 未公开确认 | 自述 staff engineer，推动团队 AI 编程 guideline | Mainline v0.1，12 个核心命令，V2EX 找深度内测 | 2026-05 V2EX 内测帖 | V2EX 私信/评论、GitHub issue | 问 5+ 人团队使用 agent 的真实误改案例和 mainline 内测要求 | https://www.v2ex.com/member/huoru | https://www.v2ex.com/t/1210451 | 2026-05-24 | 2026-05 | 能直接解释“agent 写代码为什么需要工程记忆”，适合李曼做深度访谈 | 作者/发起人 |
```

Why this works: the talent row is not a biography. It links person -> work -> current action -> evidence -> next completion field.

## 03 Good A Project Card: Enterprise Workflow / DataAgent

Historical pattern from `0523-ai-mapper.md`.

| Field | Example shape |
|---|---|
| 原始入口 | Product/tutorial pages + open cooperation page + funding/interview evidence |
| 归一化对象 | ChatExcel / 元空AI -> 逄大嵬 Davis / product team |
| 为什么能进 A | Named founder, narrow workflow, current product evidence, business/contact entry, concrete enterprise question |
| 证据链 | Product tutorial, open platform, funding/team source |
| 触达路径 | 官网客服微信 / 开放合作平台 / 商务客户微信 |
| 下一步问题 | MCP 方案、企业试点、DataAgent 真实付费场景 |
| 最终关系 | 创始人 / 产品团队 |

Legacy dense-row example. Do not copy this column order; map the facts into the current final project table schema above:

```markdown
| A | ChatExcel / 元空AI | 从 AI Excel 扩展到 DataAgent，覆盖数据获取、处理、分析、图表、PPT、ChatDB。 | AI 办公自动化 / DataAgent | 逄大嵬 Davis，北大团队创业，小团队切入 DataAgent。 | 官网、新手教程、博客、开放合作平台、融资访谈。 | 2026 官网教程覆盖 AI Excel、AI PPT、AI 文档、ChatDB。 | 已融资 · 近千万天使轮，日期待补 | 官网客服微信 / 开放合作平台 / 商务客户微信 | 通过开放合作入口问 MCP 方案、企业试点和 DataAgent 真实付费场景。 | https://chatexcel.com/blog/tutorial/chatexcel-beginners-guide/ ; https://open.chatexcel.com/ | 2026-05-23 | 2026 | 办公自动化不是泛工具，而是表格/数据工作流 Agent，产品证据、团队和触达路径清晰。 | 创始人 / 产品团队 |
```

Why this works: the row turns a product into a business-learning target. It gives a specific workflow and a concrete next completion field rather than saying "AI office is hot."

## 04 B Row That Should Not Be A Yet

Historical pattern from `0523` run report and rated output.

| Field | Example shape |
|---|---|
| 原始入口 | Media/product site around AIYouthLab / Vinsoo |
| 归一化对象 | AIYouthLab / Vinsoo -> 殷晓玥 /研发团队 |
| Why not project A | Project signal or freshness/evidence still needs one more original source; weak contact alone is not enough to block project-level A under the current policy |
| Keep as B because | Direction is relevant, but the project signal, funding detail, or current usage evidence still needs tightening |
| 下一步补全项 | Public-source check for founder personal entry, company entity, funding, and invite/contact path |

Legacy B row example. Do not copy this column order; map the facts into the current final project table schema above:

```markdown
| B / 继续观察 | AIYouthLab / Vinsoo | 云端 Agent 编程 IDE，支持本地 IDE + 云端 Agent 团队。 | Coding Agent / AI IDE | 殷晓玥，研发团队来自 UW、CMU、清华、北大和大厂。 | 已融资 · 天使轮，来源待补 | 2025-11 | Coding Agent 核心方向，00 后团队值得看，但触达和融资细节需补。 | 官网邀请码/等待名单 | 公开源补殷晓玥个人入口和公司工商。 | https://www.qbitai.com/2025/11/350485.html | https://www.aiyouthlab.com/ | 2026-05-23 | 创始人 / 研发团队 |
```

Why this works: B is not a vague maybe. It names the exact missing project-confidence fields and the future detailed-search value. If Scope, Early, Project signal, Freshness, Evidence, and Why now already pass, weak contact should be recorded as `待补触达路径` inside an A project table row instead of forcing B.

## 05 C / Background Sample

Historical pattern from `0523` rated output.

| Field | Example shape |
|---|---|
| 原始入口 | Mature open-source framework |
| 归一化对象 | AgentScope / agentscope-ai -> Alibaba-related maintainers/team |
| Why not A/B | Big-company/lab ecosystem sample, not early contactable startup lead |
| Keep as C because | Useful for technical landscape and competitor/context calibration |
| 下一步补全项 | Observe ecosystem only if the user explicitly requests big-company/lab mapping |

Legacy C row example. Do not copy this column order; map the facts into the current final project table schema above:

```markdown
| C / 轻量记录 | AgentScope / agentscope-ai | 阿里系 agent stack，覆盖 ReAct、tool、memory、planning、MCP、A2A。 | Agent framework / MCP | Dawei Gao、Zitao Li、Xuchen Pan、阿里云/阿里集团相关团队。 | 大厂/实验室背景样本 | 2026-05 | 产业级 agent infra 样本，但非早期可触达项目。 | GitHub Issues / Discord / DingTalk | 仅做技术生态观察。 | https://github.com/agentscope-ai/agentscope | https://agentscope.io/ | 2026-05-23 | 维护团队 |
```

Why this works: it preserves ecosystem signal without polluting the A/B decision list.

## 06 Output Quality Audit Case

Run report should show that rating is not arbitrary. A-class project audit rows should explain project gates and enrichment status before final rating.

```markdown
| 名称 | Scope | Early | Project signal | Evidence | Freshness | Why now | Person status | Background status | Contact status | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| Refly.AI | PASS | PASS | PASS | PASS | PASS | PASS | resolved | resolved | partial | A |
| AIYouthLab / Vinsoo | PASS | PASS | PASS | PARTIAL | PASS | PASS | resolved | partial | 待补 | B |
| AgentScope / Nexent / DeepWisdom | PASS | WEAK | PASS | PASS | PASS | WEAK | resolved | resolved | partial | C |
```

The downgrade logic should be visible:

- Contact weak alone does not block project-level A or a source-backed talent row; keep contact gaps in raw/validated notes and use `待补触达路径` only as project enrichment.
- Evidence, project signal, freshness, early status, or why-now weak -> B/C, even when topic/team are promising.
- Early weak -> C/background, even when evidence and contacts exist.
- Any closed-source factual claim should be replaced with equivalent public evidence or cause downgrade/drop.

## Rating And Downgrade Examples

Use these rules when the case is not covered by the examples above.

| Situation | Rating action |
|---|---|
| Early repo/product + current activity + original evidence + clear 李曼 project question | A project table row; mark person/contact/background as `待补` if unresolved |
| Early repo/product + named maintainer + current activity + public profile/background evidence + clear 李曼 question | A project table row and possible A talent row |
| Product/funding evidence but responsible person or contact path is weak | A project table row if project gates pass; otherwise B with concrete future detailed-search value |
| Mature company, big-company product, B-round-or-later, high financing, or stale activity | C/background unless explicitly requested |
| Ranking/index appearance only | Raw/validated lead at most; backtrace before A/B |
| Generic `contact@`, sales form, HR path, or company homepage only | Can support project-level weak contact but cannot make a talent A; missing direct contact alone cannot block a source-backed talent row |

## Common Bad Outputs

| Bad output | Why it fails | Fix |
|---|---|---|
| `项目名 + 官网 + AI方向` | No project evidence, freshness, or why-now | Backtrace to original product/repo/funding/user evidence and write what person/contact remains 待补 |
| `很热门，值得关注` | Market heat is not why-now | State the specific hypothesis 李曼 can evaluate and why now |
| `团队背景：未确认` in A talent row | A talent card requires source-backed background | Search named people or keep only project-level A with `待补团队背景` |
| `联系方式：官网/contact@` | Generic contact is weak as a personal signal | Keep as weak project contact and write a concrete future detailed-search gap |
| `榜单排名高` | Ranking is radar, not evidence | Backtrace to original product/person/activity evidence |

## Thin Row Red Flags

Before final delivery, downgrade or expand rows with:

- `未确认`, `待补`, `官网`, `contact@`, `可关注`, or market-heat-only reasons.
- Product evidence without project signal, freshness, or why-now.
- Person/team names without background facts in talent rows.
- Treating contact path as the talent-readiness signal. Talent rows need a recent action, person-project relation, and source-backed background; contact is optional context.
- Freshness based only on old media coverage, static homepage text, or stale repo activity.


## Early Stop Examples

Use these only after the selected mode's minimum gates pass.

| Case | Latest batch | Decision | Why |
|---|---|---|---|
| Pass | 30 new candidate URLs, 2 new plausible P0/P1 leads, rest duplicates/stale/mature, all four lanes have usable candidates | Stop and validate | Marginal yield is low and selected-mode minimum gates passed |
| Fail | 30 new candidate URLs, 6 new plausible P0/P1 leads, C-funding still below minimum source families | Continue recall | Yield is still meaningful and coverage gate has not passed |
| Fail | 20 new candidate URLs, 1 new lead, A-dev and D-academic empty | Continue recall | Batch is too small and lane coverage is missing |

Run-report should record: `batch_size`, `new_p0_p1_leads`, `dominant_drop_reasons`, `lane_coverage_status`, and `stop_decision`.
