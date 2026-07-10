# AI Mapper Output Schemas

Read this before writing any ai-mapper artifact.

## Table of Contents

- [Schema Stability](#schema-stability)
- [Date Requirements](#date-requirements)
- [Structured Artifacts](#structured-artifacts)
- [`validated.md`](#validatedmd)
- [`rated.md`](#ratedmd)
- [Final Report](#final-report)
- [Optional Judgment Cards](#optional-judgment-cards)

## Schema Stability

The final output structure remains project tables plus a compact talent table. Do not add a separate academic talent table, scholar list, ranking table, community-signal table, or database table. Academic papers, citations, venues, repos, demos, and labs are evidence inside project rows and `关联人才与背景`; people enter the compact talent table only when they independently qualify.

## Date Requirements

Every A/B project and talent row must distinguish:

- `source_page_date`: article/page/post/release page date.
- `true_event_date`: financing, product launch, repo/model release, paper/repo/demo event, customer/deployment, or other real event date.
- `exa_returned_date`: Exa `publishedDate` or crawl-like date if present.
- `collection_date`: run date.
- `date_decision`: which date controls freshness and why.

Use existing project date columns where possible: `采集日期` is collection date, `最近有效动态日期` is the true event date. For compact final talent tables, there are no date columns; put the absolute true event date inside `最近动作`, and put source-page/date-decision context inside `背景` only when necessary. Never use Exa returned date as `最近有效动态日期` or as the talent action date.

## Structured Artifacts

Every workspace must include `research-axes.json`, `exa-query-plan.jsonl`, `exa-query-execution.jsonl`, `exa-candidates.jsonl`, `candidates.jsonl`, and `evidence.jsonl` as defined in `references/structured-artifacts.md`. Markdown tables are for human judgment; JSON/JSONL records are for validation, repair, and dedupe. `research-axes.json` records four mandatory base research questions plus up to two enhancements; `exa-query-plan.jsonl` records deterministic source-specific queries; `exa-query-execution.jsonl` proves which planned queries ran; `exa-candidates.jsonl` preserves every Exa-returned URL before filtering; `candidates.jsonl` stores normalized kept/dropped candidates; `evidence.jsonl` stores source-backed facts. Every A/B final row should map to at least one candidate record and one non-weak evidence record.

## `validated.md`

Required sections:

- 验证汇总: 原始线索, 去重后候选, 入口类型分布, 项目类候选, 人才类候选, 暂不跟进/背景样本
- Identity Resolution table: `原始入口 | 入口类型 | 归一化对象 | 反查路径 | 结果`
- Elsewhere API discovery/supplement: required for every normal run when Elsewhere discovery/enrichment is performed; include candidate names and final disposition
- 项目类线索: `评级建议 | 名称 | 一句话描述 | AI方向 | 产品形态 | 项目背景与证据 | 关联人才与背景 | 时间有效性 | 最近动态 | 融资状态 | 触达入口 | 入库去向 | 来源平台 | 证据等级 | 证据链接`
- 人才类线索: `评级建议 | 姓名/昵称 | 关联公司/项目 | 最近动作 | 身份 | 背景 | 评级 | 证据等级 | 证据链接`
- 暂不跟进 / 背景样本
- 去重记录

## `rated.md`

Required sections:

- A/B/C 类项目: `项目名 | 一句话描述 | AI 软件细分方向 | 产品形态 | 项目背景与证据 | 融资状态 | 关联人才与背景 | 下一步补全项 | 评级 | 来源链接 | 采集日期 | 最近有效动态日期`
- 人才表: `姓名/昵称 | 关联公司/项目 | 最近动作 | 身份 | 背景 | 评级`
- 暂不跟进

## Final Report

The final top-level report must contain complete tables, not just links. It must start with a `运行状态` block that states run mode (`adaptive standard scan` / `deep map` / `blocked`), completeness (`complete`, `degraded / Exa-only`, or `blocked`), Elsewhere status, Exa status, stop reason, and practical impact.

Top A 类 contains a project table and a talent table. If no A-level talent row is resolved, keep the talent table empty or write `暂无 A 人才，待补最近动作/背景后再入表`; do not force a project into the talent table.

Every A/B/C project table uses:

```markdown
| 项目名 | 一句话描述 | AI 软件细分方向 | 产品形态 | 项目背景与证据 | 融资状态 | 关联人才与背景 | 下一步补全项 | 评级 | 来源链接 | 采集日期 | 最近有效动态日期 |
|---|---|---|---|---|---|---|---|---|---|---|---|
```

Project field requirements:

- `项目名`: primary dedupe key; include aliases/product/repo names when needed.
- `一句话描述`: make a mentor understand the project in 10 seconds; include concrete user/job/product scenario, not slogans.
- `AI 软件细分方向`: normalize to Agent, Coding, BI, 客服, 电商, 招聘, AI office, MCP, AI infra, workflow automation, security, memory, model routing, academic-system, or another concrete category.
- `产品形态`: SaaS / App / API / 插件 / 开源 / Demo / 社区项目 / 论文项目 / 模型/数据集 / 未确认; include deployment/use form when known.
- `项目背景与证据`: dense 2-4 fact summary covering what it does, true event date, current activity, product/repo/customer/demo/funding evidence, paper/venue/citation/repo/demo evidence when academic, and why the evidence is credible. Cite source type in prose and include source page date when it differs from true event date.
- `融资状态`: `未融资`, `已融资 · {轮次/金额/投资方/真实融资日期/报道日期}`, or `未确认`; write `未融资` only with explicit source support. Do not infer financing date from Exa returned date.
- `关联人才与背景`: connect to talent library. Name founder/maintainer/core team/author/lab when known and include school/company/open-source/research/product background. If unresolved, write `待补负责人/核心团队` plus what was checked.
- `下一步补全项`: future detailed-search gap, not a contact suggestion. Name the exact missing field: Background, Contact, Freshness, Funding, Evidence, Why now, Product signal, Customer/user proof, Person-project relation, or Date verification.
- `评级`: A / B / C / 暂不跟进, with a short reason inside the cell if useful.
- `来源链接`: include all material links. When Elsewhere supports a claim, include the Elsewhere URL plus any original project/product/repo/company source used for verification.
- `采集日期`: run date.
- `最近有效动态日期`: true event date, not Exa returned date.

Every A/B talent table intentionally uses the compact schema:

```markdown
| 姓名/昵称 | 关联公司/项目 | 最近动作 | 身份 | 背景 | 评级 |
|---|---|---|---|---|---|
```

Talent field requirements:

- `姓名/昵称`: named founder, core builder, maintainer, product lead, researcher-founder, or clearly identifiable team lead.
- `关联公司/项目`: company, product, repository, paper, or public work tied to the person; connect back to the project table when present.
- `最近动作`: source-backed action, preferably within the last 30 days for normal scans; include absolute true event date and action type such as financing, product launch, beta, open-source growth, demo day, roadshow, interview, paper/repo/model release, or customer/deployment proof.
- `身份`: founder, CEO, CTO, core builder, maintainer, product lead, researcher-founder, or equivalent.
- `背景`: compact, source-backed background such as school, former company, representative project, open-source/paper/product proof, funding/team fact, public profile, source label/link, and contact gap when useful. Academic facts are evidence here only when the person also qualifies for the compact talent table.
- `评级`: A/B/C with a short reason and the most important missing field if not A. A requires recent action, clear project relation, and source-backed background; B can miss one enrichment field; stale or weakly relevant people move to C/background or project enrichment.

## Optional Judgment Cards

Use a compact card only when the row is strategically important or still too dense after the table.

```markdown
### {项目名称}
- 判断：{项目级 A/B/C；是否可直接触达可选，不作为必填}
- 核心证据：{2-3 条 evidence-backed facts with source type}
- 为什么现在看：{specific hypothesis, not market heat}
- 最大不确定性：{Contact / Background / Freshness / Funding / Evidence / Why now / Project signal / Date verification}
- 下一步补全项：{what the next detailed content search should resolve; keep it concrete but not as an immediate action checklist}
```

## Other Final Sections

- 运行状态: run mode, completeness, Elsewhere status, Exa status, stop reason, and limitations
- B 类, C 类, 暂不跟进
- Elsewhere API discovery/supplement 摘要 by candidate name and disposition
- 搜索覆盖汇报 by lane
- 真实日期审计
- 来源质量复盘: `来源/平台 | 用途 | 搜索次数 | raw lead | 进入 validated | 进入 A/B | 噪声/暂不跟进 | 主要限制`
- 原始文件 links

Raw artifact concatenates A/B/C/D result files under `# AI-Mapper Raw - {MM-DD}`.

Latest pointer includes 更新时间, 搜索主题, 运行模式, 完整性状态, Elsewhere 状态, Exa 状态, 停止原因, 运行目录, 最终文件, 原始合并文件, 研究轴文件, Exa 查询计划, Exa 查询执行记录, 结构化候选文件, 结构化证据文件, 运行报告. Complete and `degraded / Exa-only` runs both use this same latest pointer path; the status lives inside the file, not in an alternate filename.
