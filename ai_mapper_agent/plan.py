from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from hashlib import sha256
import json
from typing import Any
from zoneinfo import ZoneInfo

from .contract import LANE_BUDGETS, MAX_RESULTS_PER_QUERY, TOTAL_QUERY_COUNT


@dataclass(frozen=True)
class PlanValidation:
    ok: bool
    errors: tuple[str, ...] = ()


_QUERIES: tuple[tuple[str, str], ...] = (
    ("A-dev", "中国 AI 开发者工具 开源 项目 发布"),
    ("A-dev", "中国 AI agent 开发平台 GitHub 新项目"),
    ("A-dev", "中国 AI coding 工具 产品 更新"),
    ("A-dev", "中国 AI 模型基础设施 开源 发布"),
    ("A-dev", "中国 AI workflow 自动化 产品 上线"),
    ("A-dev", "中国 AI 数据工具 初创 产品"),
    ("A-dev", "中国 AI 部署 推理 平台 新产品"),
    ("A-dev", "中国 AI 安全 评测 工具 发布"),
    ("A-dev", "中国 AI 多模态 开发工具 开源"),
    ("A-dev", "中国 AI enterprise software 开发者 产品"),
    ("B-content", "中国 AI 内容创作 软件 产品 发布"),
    ("B-content", "中国 AI 视频生成 工具 新产品"),
    ("B-content", "中国 AI 图像设计 软件 更新"),
    ("B-content", "中国 AI 音频播客 工具 发布"),
    ("B-content", "中国 AI 营销 内容 软件 初创"),
    ("B-content", "中国 AI 教育 内容 产品 更新"),
    ("B-content", "中国 AI 搜索 知识产品 发布"),
    ("B-content", "中国 AI 内容工作流 创业公司"),
    ("C-funding", "中国 AI 软件 融资 种子轮"),
    ("C-funding", "中国 AI agent 融资 初创公司"),
    ("C-funding", "中国 AI SaaS 融资 产品"),
    ("C-funding", "中国 AI 开源 创业 融资"),
    ("C-funding", "中国生成式 AI 软件 融资"),
    ("C-funding", "中国企业 AI 软件 融资"),
    ("C-funding", "中国 AI 应用 天使轮"),
    ("C-funding", "中国 AI 工具 创业公司 投资"),
    ("C-funding", "中国 AI 基础设施 初创 融资"),
    ("C-funding", "China AI software startup funding"),
    ("C-funding", "China AI agent startup investment"),
    ("C-funding", "China generative AI product seed funding"),
    ("C-funding", "China AI developer tools venture funding"),
    ("C-funding", "中国 AI 软件 公司 新一轮融资"),
    ("D-academic", "中国 AI 论文 开源 项目 产品化"),
    ("D-academic", "中国 AI 研究团队 创业 产品"),
    ("D-academic", "中国 AI agent 论文 代码 发布"),
    ("D-academic", "中国 AI 多模态 论文 开源 软件"),
    ("D-academic", "中国 AI 具身智能 研究 项目"),
    ("D-academic", "中国 AI 学术成果 产品化"),
    ("D-academic", "China AI research open source product"),
    ("D-academic", "中国 AI 顶会论文 创业团队"),
)


def build_query_plan(
    *, topic: str | None, run_date: date, timezone_name: str = "Asia/Shanghai"
) -> list[dict[str, Any]]:
    """Return the only permitted 40 logical Exa requests for one run."""
    topic_filter = f" {topic.strip()}" if topic and topic.strip() else ""
    start_date = run_date - timedelta(days=29)
    zone = ZoneInfo(timezone_name)
    start_boundary = datetime.combine(start_date, time.min, tzinfo=zone).isoformat(timespec="seconds")
    end_boundary = datetime.combine(run_date + timedelta(days=1), time.min, tzinfo=zone).isoformat(timespec="seconds")
    return [
        {
            "query_id": f"q{index:02d}",
            "lane": lane,
            "query": f"{query}{topic_filter}",
            "type": "auto",
            "num_results": MAX_RESULTS_PER_QUERY,
            "start_published_date": start_boundary,
            "end_published_date": end_boundary,
        }
        for index, (lane, query) in enumerate(_QUERIES, start=1)
    ]


def validate_query_plan(rows: list[dict[str, Any]]) -> PlanValidation:
    errors: list[str] = []
    if len(rows) != TOTAL_QUERY_COUNT:
        errors.append("QUERY_PLAN_COUNT")
    expected_ids = {f"q{index:02d}" for index in range(1, TOTAL_QUERY_COUNT + 1)}
    if {row.get("query_id") for row in rows} != expected_ids:
        errors.append("QUERY_PLAN_IDS")
    if Counter(row.get("lane") for row in rows) != LANE_BUDGETS:
        errors.append("QUERY_PLAN_LANES")
    if any(row.get("type") != "auto" for row in rows):
        errors.append("QUERY_PLAN_MODE")
    if any(row.get("num_results") != MAX_RESULTS_PER_QUERY for row in rows):
        errors.append("QUERY_PLAN_RESULTS")
    return PlanValidation(ok=not errors, errors=tuple(errors))


def plan_hash(rows: list[dict[str, Any]]) -> str:
    return sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
