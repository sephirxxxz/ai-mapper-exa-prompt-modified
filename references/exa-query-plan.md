# AI Mapper EXA Query Plan

Read this before the first Exa request. The query plan separates semantic judgment from mechanical search expansion.

## Contract

The agent writes `{WORKSPACE}/research-axes.json` with:

- exactly four mandatory base axes;
- zero to two enhancement axes;
- stable topic vocabulary only, without years, months, recruitment terms, or source restrictions;
- a natural-language `ranking_question` describing what an ideal result proves;
- candidate types, evidence targets, lane affinity, weight, and exclusions.

The mandatory base roles are:

| `base_role` | Required lane | Question answered |
|---|---|---|
| `developer-product` | `A-dev` | What was shipped by developers or product teams? |
| `product-market` | `B-content` | What product, customer, deployment, or market proof exists? |
| `funding-company` | `C-funding` | What early financing or company event occurred? |
| `academic-productization` | `D-academic` | What paper/system/model became a repo, demo, product, or startup signal? |

Enhancement axes use `axis_type: "enhancement"` and `base_role: null`. They may widen a user-emphasized direction or a current high-value theme, but cannot replace a base axis.

When an enhancement axis targets a lane, the compiler reserves a bounded share of that lane's query floor for enhancements: 20% by default. Base axes retain the remaining budget, so an emphasized theme widens recall without crowding out mandatory coverage.

## Why 4-6 Axes

AI Mapper is a broad unknown-candidate scan, not a single-topic report. Four base axes protect coverage across the four recall lanes. Up to two enhancement axes add current or user-emphasized themes without allowing semantic query expansion to create uncontrolled duplication.

The compiler expands axes through lane-specific source packs and the selected run mode:

```text
research axis × source family × query variant × date window
```

Standard mode produces at least 40 planned queries. Deep map produces at least 115. Counts come from `references/run-modes.json`.

## Required Schema

```json
{
  "schema_version": "1.0",
  "topic": "通用扫描",
  "objective": "发现中国相关早期 AI 软件项目与人才",
  "collection_date": "2026-07-09",
  "priority_window": {
    "start": "2026-06-09",
    "end": "2026-07-09"
  },
  "axes": [
    {
      "axis_id": "developer-product",
      "axis_type": "base",
      "base_role": "developer-product",
      "label": "开发者与产品发布",
      "ranking_question": "最近有哪些中国相关开发者或早期团队发布了可验证的 AI 软件产品、Repo、模型或 Demo？",
      "search_seed": "中国 AI Agent MCP Coding Agent 开源 产品发布",
      "candidate_types": ["project", "repo", "person"],
      "evidence_targets": ["true event date", "repo or release", "product proof"],
      "lane_affinity": ["A-dev"],
      "weight": 1.0,
      "exclusions": ["成熟公司", "B轮及以后", "招聘信息"]
    },
    {
      "axis_id": "product-market",
      "axis_type": "base",
      "base_role": "product-market",
      "label": "产品与市场验证",
      "ranking_question": "最近哪些中国相关 AI 软件项目出现了用户、客户、部署或商业化证据？",
      "search_seed": "中国 AI 软件 产品 客户 部署 商业化 创始人",
      "candidate_types": ["project", "company", "founder"],
      "evidence_targets": ["customer proof", "deployment", "founder relation"],
      "lane_affinity": ["B-content"],
      "weight": 0.9,
      "exclusions": ["纯观点内容", "工具目录", "招聘信息"]
    },
    {
      "axis_id": "funding-company",
      "axis_type": "base",
      "base_role": "funding-company",
      "label": "早期融资与公司事件",
      "ranking_question": "最近哪些中国相关早期 AI 软件公司公开了天使轮、种子轮、Pre-A 或可核验的投资事件？",
      "search_seed": "中国 AI Agent AI软件 融资 天使轮 种子轮 Pre-A",
      "candidate_types": ["company", "project", "founder"],
      "evidence_targets": ["funding round", "investor", "true event date"],
      "lane_affinity": ["C-funding"],
      "weight": 1.0,
      "exclusions": ["B轮及以后", "大额成熟项目", "数据库摘要"]
    },
    {
      "axis_id": "academic-productization",
      "axis_type": "base",
      "base_role": "academic-productization",
      "label": "论文系统与产品化",
      "ranking_question": "最近哪些中国研究团队把 AI 论文、系统、模型或 Benchmark 推进成了 Repo、Demo、产品或创业项目？",
      "search_seed": "中国 AI Agent 论文 系统 模型 repo demo 产品化",
      "candidate_types": ["paper", "repo", "project", "person"],
      "evidence_targets": ["paper date", "repo or demo", "application potential"],
      "lane_affinity": ["D-academic"],
      "weight": 0.8,
      "exclusions": ["无项目化产物", "无应用路径", "招聘信息"]
    }
  ]
}
```

## Compile And Execute

Compile before any Exa request:

```bash
python3 scripts/build_exa_query_plan.py compile \
  --workspace "$WORKSPACE" \
  --run-mode "$RUN_MODE"
```

This writes `{WORKSPACE}/exa-query-plan.jsonl`. Execute only rows from that file.

Persist every Exa response using its planned query id:

```bash
python3 scripts/forced_pipeline.py record-exa-response \
  --workspace "$WORKSPACE" \
  --query-plan-file "$WORKSPACE/exa-query-plan.jsonl" \
  --query-id "$QUERY_ID" \
  --response-file "$RESPONSE_FILE" \
  --collection-date "$COLLECTION_DATE" \
  --run-mode "$RUN_MODE"
```

The command writes:

- returned URLs to `exa-candidates.jsonl`;
- one execution record to `exa-query-execution.jsonl`;
- `status=completed` when usable URLs were returned;
- `status=queried_no_usable_result` when the query ran but returned no usable URL.

Do not create fake candidate rows for zero-result queries. Do not run freehand Exa recall after compilation.

## Evidence Boundary

`ranking_question`, `search_seed`, `exa_query`, Exa rank, highlights, snippets, and execution status are routing/audit data only. They cannot support final claims. Original openable pages remain the evidence source.
