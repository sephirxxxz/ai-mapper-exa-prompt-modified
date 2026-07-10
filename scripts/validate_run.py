#!/usr/bin/env python3
"""Validate ai-mapper skill package or run artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


LANES = ("A-dev", "B-content", "C-funding", "D-academic")

REQUIRED_SKILL_REFS = (
    "references/exa-query-plan.md",
    "references/exa-query-packs.json",
    "references/source-policy.md",
    "references/schemas.md",
    "references/rating-rubric.md",
    "references/blockers.md",
    "references/run-modes.md",
    "references/run-modes.json",
    "references/run-states.md",
    "references/source-families.md",
    "references/structured-artifacts.md",
    "references/pressure-tests.md",
)

REQUIRED_WORKSPACE_FILES = (
    "topic.md",
    "topics.md",
    "research-axes.json",
    "exa-query-plan.jsonl",
    "exa-query-execution.jsonl",
    "validated.md",
    "rated.md",
    "exa-candidates.jsonl",
    "candidates.jsonl",
    "evidence.jsonl",
    "AI项目与人才Mapping.md",
    "run-report.md",
)

BANNED_RECRUITING_TERMS = ("Boss直聘", "拉勾", "猎聘", "脉脉招聘")
BANNED_RECRUITING_RE = re.compile(
    r"(Boss\s*直聘|BOSS\s*直聘|拉勾|猎聘|脉脉招聘|招聘页|岗位页|招聘海报|hiring\s*(page|post|poster)|job\s*(board|post|posting))",
    re.I,
)

PROJECT_TABLE_HEADER = "| 项目名 | 一句话描述 | AI 软件细分方向 | 产品形态 | 项目背景与证据 | 融资状态 | 关联人才与背景 | 下一步补全项 | 评级 | 来源链接 | 采集日期 | 最近有效动态日期 |"
TALENT_TABLE_HEADER = "| 姓名/昵称 | 关联公司/项目 | 最近动作 | 身份 | 背景 | 评级 |"
VALIDATED_TALENT_HEADER = "人才类线索: `评级建议 | 姓名/昵称 | 关联公司/项目 | 最近动作 | 身份 | 背景 | 评级 | 证据等级 | 证据链接`"

FORBIDDEN_SCHEMA_DRIFT_TERMS = (
    "Do not replace it with a compact talent table",
    "完整人才表",
    "人才表: `姓名/昵称 | 一句话介绍 | 身份 | 方向 | 关联项目 | 人才背景与证据 | 最近动态 | 联系入口 | 下一步补全项 | 评级 | 平台主页 | 来源链接 | 采集日期 | 最近有效动态日期`",
    "| 姓名/昵称 | 一句话介绍 | 身份 | 方向 | 关联项目 | 人才背景与证据 | 最近动态 | 联系入口 | 下一步补全项 | 评级 | 平台主页 | 来源链接 | 采集日期 | 最近有效动态日期 |",
)

REQUIRED_MODERNIZED_SKILL_TERMS = (
    "Normal runs are recency-first",
    "Recency Gate",
    "Priority Objective",
    "Recall Volume Gate",
    "Source Coverage Gate",
    "Exa Search Quantity Gate",
    "Elsewhere Financing Pass",
    "adaptive standard scan",
    "references/run-modes.md",
    "references/run-states.md",
    "references/source-families.md",
    "references/structured-artifacts.md",
    "degraded / Exa-only",
    "standard final/raw/latest paths",
    "true_event_date",
    "Product Hunt",
    "GitHub Trending",
    "Hugging Face Trending",
    "Do not create a separate academic talent table",
    "exa-candidates.jsonl",
)

EXA_CANDIDATE_REQUIRED = {
    "record_id", "plan_id", "query_id", "axis_id", "lane", "exa_query",
    "query_batch_id", "source_family_planned", "returned_rank",
    "url", "normalized_url", "domain", "title", "source_type_hint",
    "source_family_hint", "entry_type_hint", "possible_signal", "risk_reason",
    "entity_cluster_id", "must_open_reason", "review_decision",
    "exa_returned_date", "exa_published_date", "exa_crawl_date",
    "highlight_or_snippet", "why_it_might_matter", "collection_date",
    "run_mode", "selected_for_review", "fetch_status", "keep_drop_status",
    "keep_drop_reason", "candidate_id",
}
QUERY_PLAN_REQUIRED = {
    "schema_version", "plan_id", "query_id", "axis_id", "lane",
    "source_family", "exa_query", "ranking_question", "candidate_types",
    "evidence_targets", "priority", "run_mode", "collection_date",
    "priority_window_start", "priority_window_end", "execution_status",
}
QUERY_EXECUTION_REQUIRED = {
    "schema_version", "plan_id", "query_id", "axis_id", "lane",
    "source_family", "exa_query", "status", "result_count",
    "collection_date",
}
BASE_ROLES = {
    "developer-product",
    "product-market",
    "funding-company",
    "academic-productization",
}
AXIS_REQUIRED = {
    "axis_id", "axis_type", "base_role", "label", "ranking_question",
    "search_seed", "candidate_types", "evidence_targets", "lane_affinity",
    "weight", "exclusions",
}
QUERY_EXECUTION_STATUSES = {"completed", "queried_no_usable_result"}

CANDIDATE_REQUIRED = {
    "candidate_id", "name", "entry_type", "lane", "source_origin", "run_mode",
    "status", "rating", "gap_type", "evidence_ids", "notes",
}
EVIDENCE_REQUIRED = {
    "evidence_id", "candidate_id", "url", "source_family", "source_type",
    "evidence_level", "claim_supported", "source_page_date", "true_event_date",
    "exa_returned_date", "collection_date", "date_decision", "openable_status",
}
STATUS_RECORD_REQUIRED = {
    "record_type", "status", "run_mode", "blocker_reason", "collection_date", "notes",
}
OPENED_FETCH_STATUSES = {"opened", "fetched", "blocked"}
EXA_FETCH_STATUSES = {"pending", "opened", "fetched", "blocked"}
EXA_KEEP_DROP_STATUSES = {
    "", "kept", "dropped", "not_selected", "unreviewed", "stale", "duplicate", "blocked", "background",
}
EXA_MUST_OPEN_REASONS = {
    "official_source", "funding_source", "investor_or_vc_source", "repo_or_model_source",
    "paper_or_project_source", "query_top_result", "source_family_coverage", "cluster_representative",
    "long_tail_audit", "none",
}
OPENABLE_STATUSES = {"opened", "fetched", "blocked", "paywall", "captcha", "closed", "not_needed"}
EVIDENCE_LEVELS = {"S", "A", "B", "C", "无效"}
SEARCH_LAYER_SOURCE_RE = re.compile(r"(exa|context[-_ ]?mode|snippet|summary|highlight)", re.I)
DATE_FIELDS = {
    "exa_returned_date", "exa_published_date", "exa_crawl_date", "collection_date",
    "source_page_date", "true_event_date",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T\s].*)?$")
EMPTY_DATE_VALUES = {"", "none", "null", "unknown", "n/a", "na", "not_applicable", "待补", "未确认", "不适用"}
WEAK_DEGRADED_RE = re.compile(r"完整性状态\s*[:：]\s*degraded(?!\s*/\s*Exa-only)", re.I)
FORBIDDEN_ELSEWHERE_ENRICHMENT_RE = re.compile(
    r"(待补\s*Elsewhere\s*enrichment|Elsewhere\s+enrichment|Elsewhere coverage gap)",
    re.I,
)
TEAM_PERSON_ELSEWHERE_GAP_RE = re.compile(
    r"(团队|人员|负责人|核心团队|背景|Person|Team|Background|Contact)[^|\n]{0,80}(待补\s*Elsewhere|Elsewhere\s+gap)",
    re.I,
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def exists(path: Path, errors: list[str], label: str | None = None) -> None:
    if not path.exists():
        errors.append(f"missing {label or path}")


def require_text(text: str, needle: str, errors: list[str], label: str) -> None:
    if needle not in text:
        errors.append(f"{label}: missing {needle!r}")


def forbid_text(text: str, needle: str, errors: list[str], label: str) -> None:
    if needle in text:
        errors.append(f"{label}: forbidden {needle!r}")


def forbid_recruiting_text(text: str, errors: list[str], label: str) -> None:
    match = BANNED_RECRUITING_RE.search(text)
    if match:
        errors.append(f"{label}: forbidden recruiting/job-board term {match.group(0)!r}")


def forbid_elsewhere_team_person_gap(text: str, errors: list[str], label: str) -> None:
    match = FORBIDDEN_ELSEWHERE_ENRICHMENT_RE.search(text)
    if match:
        errors.append(
            f"{label}: forbidden Elsewhere-as-enrichment option {match.group(0)!r}; "
            "use public-web/Codex search gaps for team/person/background"
        )
    match = TEAM_PERSON_ELSEWHERE_GAP_RE.search(text)
    if match:
        errors.append(
            f"{label}: team/person/background gaps cannot use Elsewhere as next-step wording: "
            f"{match.group(0)!r}"
        )


def first_int(text: str) -> int | None:
    match = re.search(r"\d[\d,]*", text)
    if not match:
        return None
    return int(match.group(0).replace(",", ""))


def gate_actual(text: str, gate_name: str) -> int | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 5 and cells[0] == gate_name:
            return first_int(cells[2])
    return None


def non_status_jsonl_count(path: Path) -> int | None:
    if not path.exists():
        return None
    count = 0
    for line in read(path).splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("record_type") != "status":
            count += 1
    return count


def is_valid_date_like(value: object) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if text.lower() in EMPTY_DATE_VALUES:
        return True
    return bool(DATE_RE.match(text))


def is_ab_rating(value: object) -> bool:
    text = str(value)
    return text.startswith("A") or text.startswith("B") or "重点关注" in text or "继续观察" in text


def load_jsonl(path: Path, errors: list[str], label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for i, line in enumerate(read(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("record_type") != "status":
            rows.append(obj)
        elif not isinstance(obj, dict):
            errors.append(f"{label}:{i}: JSONL row must be an object")
    return rows


def load_run_modes(skill_dir: Path) -> dict[str, Any]:
    path = skill_dir / "references" / "run-modes.json"
    if not path.exists():
        return {}
    return json.loads(read(path))


def mode_gate_minimums(run_modes: dict[str, Any], mode: str) -> dict[str, int]:
    modes = run_modes.get("modes", {}) if run_modes else {}
    selected = modes.get(mode) or modes.get("adaptive standard scan") or {}
    gates = selected.get("gates", {})
    return {gate: int(spec["minimum"]) for gate, spec in gates.items() if isinstance(spec, dict) and "minimum" in spec}


def selected_mode(text: str) -> str:
    if re.search(r"(run[_ -]?mode|运行模式|模式)\s*[:：]?\s*(deep map|deep|深度)", text, re.I):
        return "deep map"
    return "adaptive standard scan"


def validate_gate_table(text: str, errors: list[str], run_modes: dict[str, Any]) -> None:
    require_text(text, "| Gate | Required | Actual | Pass? | Notes |", errors, "run-report.md")
    if WEAK_DEGRADED_RE.search(text):
        errors.append("run-report.md: use exact completeness `degraded / Exa-only`, not bare `degraded`")
    degraded = "degraded / Exa-only" in text
    gate_minimums = mode_gate_minimums(run_modes, selected_mode(text))
    if not gate_minimums:
        errors.append("run-report.md: no gate minimums loaded from references/run-modes.json")
        return

    seen: dict[str, tuple[int | None, str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        gate, required_text, actual_text, pass_text, _notes = cells[:5]
        if gate in gate_minimums:
            required = first_int(required_text)
            minimum = gate_minimums[gate]
            if required != minimum:
                errors.append(
                    f"run-report.md: gate {gate!r} Required {required!r} does not match selected-mode minimum {minimum}"
                )
            seen[gate] = (first_int(actual_text), pass_text.upper())

    for gate, minimum in gate_minimums.items():
        if gate not in seen:
            errors.append(f"run-report.md: missing gate table row {gate!r}")
            continue
        actual, pass_text = seen[gate]
        if degraded and gate == "Elsewhere financing/startup candidate facts":
            if actual is None:
                errors.append(f"run-report.md: gate {gate!r} missing numeric Actual")
            if pass_text not in {"DEGRADED", "N/A", "PARTIAL", "FAIL"}:
                errors.append(f"run-report.md: degraded Elsewhere gate should be marked DEGRADED/N/A/PARTIAL/FAIL, got {pass_text!r}")
            continue
        if actual is None:
            errors.append(f"run-report.md: gate {gate!r} missing numeric Actual")
        elif actual < minimum:
            errors.append(f"run-report.md: gate {gate!r} actual {actual} below minimum {minimum}")
        if pass_text != "PASS":
            errors.append(f"run-report.md: gate {gate!r} Pass? must be PASS, got {pass_text!r}")


def validate_jsonl(path: Path, required: set[str], errors: list[str], label: str) -> list[dict[str, Any]]:
    exists(path, errors, label)
    if not path.exists():
        return []
    text = read(path).strip()
    if not text:
        errors.append(f"{label}: empty JSONL; use a status record for blocked runs")
        return []
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), 1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{label}:{i}: invalid JSON: {exc}")
            continue
        if not isinstance(obj, dict):
            errors.append(f"{label}:{i}: JSONL row must be an object")
            continue
        if obj.get("record_type") == "status":
            missing = STATUS_RECORD_REQUIRED - set(obj)
            if missing:
                errors.append(f"{label}:{i}: status record missing keys {sorted(missing)}")
            if obj.get("status") != "blocked":
                errors.append(f"{label}:{i}: status record must use status=blocked")
            continue
        rows.append(obj)
        missing = required - set(obj)
        if missing:
            errors.append(f"{label}:{i}: missing keys {sorted(missing)}")
        if label == "exa-candidates.jsonl":
            must_open_reason = str(obj.get("must_open_reason", ""))
            fetch_status = str(obj.get("fetch_status", ""))
            keep_drop_status = str(obj.get("keep_drop_status", ""))
            selected = obj.get("selected_for_review")
            if fetch_status not in EXA_FETCH_STATUSES:
                errors.append(f"{label}:{i}: invalid fetch_status={fetch_status!r}")
            if keep_drop_status not in EXA_KEEP_DROP_STATUSES:
                errors.append(f"{label}:{i}: invalid keep_drop_status={keep_drop_status!r}")
            if must_open_reason not in EXA_MUST_OPEN_REASONS:
                errors.append(f"{label}:{i}: invalid must_open_reason={must_open_reason!r}")
            if must_open_reason and must_open_reason != "none":
                if selected is not True:
                    errors.append(f"{label}:{i}: must-open row must set selected_for_review=true")
                if fetch_status not in OPENED_FETCH_STATUSES:
                    errors.append(f"{label}:{i}: must-open row has fetch_status={fetch_status!r}")
            if keep_drop_status == "dropped" and fetch_status not in OPENED_FETCH_STATUSES:
                errors.append(f"{label}:{i}: unopened/unblocked row cannot use keep_drop_status=dropped")
        if label == "evidence.jsonl":
            if str(obj.get("openable_status", "")) not in OPENABLE_STATUSES:
                errors.append(f"{label}:{i}: invalid openable_status={obj.get('openable_status')!r}")
            if str(obj.get("evidence_level", "")) not in EVIDENCE_LEVELS:
                errors.append(f"{label}:{i}: invalid evidence_level={obj.get('evidence_level')!r}")
            source_type = str(obj.get("source_type", ""))
            if SEARCH_LAYER_SOURCE_RE.search(source_type):
                errors.append(f"{label}:{i}: source_type cannot be search-layer evidence: {source_type!r}")
        for field in DATE_FIELDS & set(obj):
            if not is_valid_date_like(obj.get(field)):
                errors.append(f"{label}:{i}: invalid date in {field}={obj.get(field)!r}")
    return rows


def validate_skill_dir(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    agent_yaml = skill_dir / "agents" / "openai.yaml"

    exists(skill_md, errors)
    exists(agent_yaml, errors)
    for rel in REQUIRED_SKILL_REFS:
        exists(skill_dir / rel, errors, rel)
    exists(skill_dir / "scripts" / "preflight.py", errors, "scripts/preflight.py")
    exists(
        skill_dir / "scripts" / "build_exa_query_plan.py",
        errors,
        "scripts/build_exa_query_plan.py",
    )
    exists(skill_dir / "scripts" / "validate_run.py", errors, "scripts/validate_run.py")

    run_modes = load_run_modes(skill_dir)
    if run_modes:
        modes = run_modes.get("modes", {})
        for mode in ("adaptive standard scan", "deep map"):
            if mode not in modes:
                errors.append(f"references/run-modes.json: missing mode {mode!r}")
            elif not mode_gate_minimums(run_modes, mode):
                errors.append(f"references/run-modes.json: mode {mode!r} has no gate minimums")

    if (skill_dir / ".DS_Store").exists():
        errors.append("remove .DS_Store from skill package")

    if skill_md.exists():
        skill = read(skill_md)
        for needle in (
            "Elsewhere API is mandatory", "Always set `TOPIC=通用扫描`",
            "references/source-policy.md", "references/schemas.md", "references/rating-rubric.md",
            "references/blockers.md", "references/run-modes.md", "references/run-states.md",
            "references/source-families.md", "references/structured-artifacts.md",
            "references/pressure-tests.md", "references/exa-query-plan.md",
            "research-axes.json", "exa-query-plan.jsonl",
            "exa-query-execution.jsonl", "scripts/build_exa_query_plan.py",
            "scripts/preflight.py", "scripts/validate_run.py",
        ):
            require_text(skill, needle, errors, "SKILL.md")
        for forbidden in ("When connected or explicitly requested", "Do not use Elsewhere when", "uses Elsewhere API checks when available"):
            forbid_text(skill, forbidden, errors, "SKILL.md")
        for term in REQUIRED_MODERNIZED_SKILL_TERMS:
            require_text(skill, term, errors, "SKILL.md")

    for rel in ("SKILL.md", "references/source-policy.md", "references/rating-rubric.md", "references/schemas.md"):
        path = skill_dir / rel
        if path.exists():
            text = read(path)
            for term in FORBIDDEN_SCHEMA_DRIFT_TERMS:
                forbid_text(text, term, errors, rel)
            forbid_elsewhere_team_person_gap(text, errors, rel)

    for rel in ("references/blockers.md", "references/run-states.md", "references/pressure-tests.md"):
        path = skill_dir / rel
        if path.exists():
            forbid_elsewhere_team_person_gap(read(path), errors, rel)

    schemas = skill_dir / "references" / "schemas.md"
    if schemas.exists():
        schema_text = read(schemas)
        require_text(schema_text, VALIDATED_TALENT_HEADER, errors, "references/schemas.md")
        require_text(schema_text, TALENT_TABLE_HEADER, errors, "references/schemas.md")
        require_text(schema_text, "exa-candidates.jsonl", errors, "references/schemas.md")
        require_text(schema_text, "research-axes.json", errors, "references/schemas.md")
        require_text(schema_text, "exa-query-plan.jsonl", errors, "references/schemas.md")
        require_text(schema_text, "exa-query-execution.jsonl", errors, "references/schemas.md")
        require_text(schema_text, "candidates.jsonl", errors, "references/schemas.md")
        require_text(schema_text, "evidence.jsonl", errors, "references/schemas.md")

    required_ref_terms = {
        "references/run-modes.md": ("adaptive standard scan", "Minimum | Target | Cap", "Early Stop Rule", "marginal yield", "deep map", "run-modes.json"),
        "references/run-states.md": ("complete", "degraded / Exa-only", "blocked", "Required Status Block"),
        "references/source-families.md": ("Allowed Source Families", "Banned Or Non-Counting Families", "queried/no usable result"),
        "references/exa-query-plan.md": ("four mandatory base axes", "enhancement axes", "ranking_question", "queried_no_usable_result"),
        "references/structured-artifacts.md": ("research-axes.json", "exa-query-plan.jsonl", "exa-query-execution.jsonl", "exa-candidates.jsonl", "candidates.jsonl", "evidence.jsonl", "Required keys", "Validation Rules"),
        "references/pressure-tests.md": ("C-funding has 8-15 decent leads", "hard-code 300 or 600", "exa-query-plan.jsonl", "exa-query-execution.jsonl", "exa-candidates.jsonl", "candidates.jsonl", "Gate | Required | Actual | Pass? | Notes"),
        "references/rating-rubric.md": ("Gap Enum", "Evidence", "Funding", "Elsewhere", "Public evidence"),
    }
    for rel, terms in required_ref_terms.items():
        path = skill_dir / rel
        if path.exists():
            content = read(path)
            for term in terms:
                require_text(content, term, errors, rel)

    if agent_yaml.exists():
        agent = read(agent_yaml)
        forbid_text(agent, "four search subagents", errors, "agents/openai.yaml")
        require_text(agent, "TOPIC=通用扫描", errors, "agents/openai.yaml")

    return errors


def validate_lane_file(path: Path, errors: list[str]) -> None:
    exists(path, errors)
    if not path.exists():
        return
    text = read(path)
    require_text(text, "## Exa Candidate Queue", errors, path.name)
    require_text(text, "| Exa query | Candidate URL | Why it might matter | Opened/fetched? | Keep/drop reason |", errors, path.name)
    require_text(text, "| 名称 | 入口类型 | 类型 | 一句话描述 | 赛道 | 找谁 | 为什么找 | 怎么找 | 找了之后问什么 | 最近动态 | 主证据链接 | 补充证据链接 | 联系入口 | 证据等级 | 备注 |", errors, path.name)
    require_text(text, "搜索次数", errors, path.name)
    for term in BANNED_RECRUITING_TERMS:
        forbid_text(text, term, errors, path.name)
    forbid_recruiting_text(text, errors, path.name)


def validate_structured_links(
    exa_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    errors: list[str],
) -> None:
    seen_record_ids: set[str] = set()
    seen_query_rank: set[tuple[str, str, str]] = set()
    seen_normalized_urls: set[str] = set()
    for i, row in enumerate(exa_rows, 1):
        record_id = str(row.get("record_id", ""))
        if record_id in seen_record_ids:
            errors.append(f"exa-candidates.jsonl:{i}: duplicate record_id {record_id!r}")
        seen_record_ids.add(record_id)

        query_rank = (str(row.get("lane", "")), str(row.get("query_batch_id", "")), str(row.get("returned_rank", "")))
        if query_rank in seen_query_rank:
            errors.append(f"exa-candidates.jsonl:{i}: duplicate lane/query_batch_id/returned_rank {query_rank!r}")
        seen_query_rank.add(query_rank)

        normalized_url = str(row.get("normalized_url", "")).strip()
        if normalized_url:
            if normalized_url in seen_normalized_urls:
                errors.append(f"exa-candidates.jsonl:{i}: duplicate normalized_url {normalized_url!r}")
            seen_normalized_urls.add(normalized_url)

    candidate_ids = {str(row.get("candidate_id")) for row in candidate_rows if row.get("candidate_id")}
    evidence_by_id = {str(row.get("evidence_id")): row for row in evidence_rows if row.get("evidence_id")}
    evidence_by_candidate: dict[str, list[dict[str, Any]]] = {}
    for i, row in enumerate(evidence_rows, 1):
        candidate_id = str(row.get("candidate_id", ""))
        if candidate_id not in candidate_ids:
            errors.append(f"evidence.jsonl:{i}: evidence candidate_id {candidate_id!r} does not exist in candidates.jsonl")
        evidence_by_candidate.setdefault(candidate_id, []).append(row)

    for i, row in enumerate(candidate_rows, 1):
        candidate_id = str(row.get("candidate_id", ""))
        evidence_ids = row.get("evidence_ids", [])
        if not isinstance(evidence_ids, list):
            errors.append(f"candidates.jsonl:{i}: evidence_ids must be an array")
            evidence_ids = []
        missing_evidence_ids = [evidence_id for evidence_id in evidence_ids if str(evidence_id) not in evidence_by_id]
        if missing_evidence_ids:
            errors.append(f"candidates.jsonl:{i}: missing evidence ids {missing_evidence_ids!r}")

        if is_ab_rating(row.get("rating")):
            supporting = [
                evidence_by_id[str(evidence_id)]
                for evidence_id in evidence_ids
                if str(evidence_id) in evidence_by_id
                and evidence_by_id[str(evidence_id)].get("candidate_id") == candidate_id
                and evidence_by_id[str(evidence_id)].get("openable_status") in {"opened", "fetched"}
                and evidence_by_id[str(evidence_id)].get("evidence_level") != "无效"
            ]
            if not supporting:
                errors.append(
                    f"candidates.jsonl:{i}: A/B candidate {candidate_id!r} lacks opened/fetched non-无效 evidence"
                )
            if not any(str(ev.get("true_event_date", "")).strip() for ev in supporting) and not str(row.get("notes", "")).strip():
                errors.append(f"candidates.jsonl:{i}: A/B candidate {candidate_id!r} lacks true_event_date/date_decision support")


def validate_query_artifacts(
    workspace: Path,
    exa_rows: list[dict[str, Any]],
    errors: list[str],
) -> None:
    axes_path = workspace / "research-axes.json"
    axis_ids: set[str] = set()
    if axes_path.exists():
        try:
            axes_payload = json.loads(read(axes_path))
        except json.JSONDecodeError as exc:
            errors.append(f"research-axes.json: invalid JSON: {exc}")
            axes_payload = {}
        blocked_axes = (
            isinstance(axes_payload, dict)
            and axes_payload.get("record_type") == "status"
            and axes_payload.get("status") == "blocked"
        )
        if blocked_axes:
            missing = STATUS_RECORD_REQUIRED - set(axes_payload)
            if missing:
                errors.append(
                    f"research-axes.json: status record missing keys "
                    f"{sorted(missing)}"
                )
        if not blocked_axes:
            if axes_payload.get("topic") != "通用扫描":
                errors.append("research-axes.json: topic must be 通用扫描")
            axes = (
                axes_payload.get("axes")
                if isinstance(axes_payload, dict)
                else None
            )
            if not isinstance(axes, list) or not 4 <= len(axes) <= 6:
                errors.append(
                    "research-axes.json: axes must contain between 4 and 6 items"
                )
                axes = []
            roles: list[str] = []
            covered_lanes: set[str] = set()
            enhancement_count = 0
            for index, row in enumerate(axes, 1):
                if not isinstance(row, dict):
                    errors.append(
                        f"research-axes.json: axis {index} must be an object"
                    )
                    continue
                missing = AXIS_REQUIRED - set(row)
                if missing:
                    errors.append(
                        f"research-axes.json: axis {index} missing keys "
                        f"{sorted(missing)}"
                    )
                axis_id = str(row.get("axis_id") or "")
                if not axis_id:
                    errors.append(
                        f"research-axes.json: axis {index} missing axis_id"
                    )
                elif axis_id in axis_ids:
                    errors.append(
                        f"research-axes.json: duplicate axis_id {axis_id}"
                    )
                axis_ids.add(axis_id)
                if row.get("axis_type") == "base":
                    roles.append(str(row.get("base_role") or ""))
                elif row.get("axis_type") == "enhancement":
                    enhancement_count += 1
                    if row.get("base_role") not in {None, ""}:
                        errors.append(
                            f"research-axes.json: enhancement {axis_id} "
                            "must use base_role=null"
                        )
                else:
                    errors.append(
                        f"research-axes.json: axis {axis_id} has invalid "
                        f"axis_type {row.get('axis_type')!r}"
                    )
                lanes = row.get("lane_affinity")
                if isinstance(lanes, list):
                    covered_lanes.update(str(lane) for lane in lanes)
            if set(roles) != BASE_ROLES or len(roles) != len(BASE_ROLES):
                errors.append(
                    "research-axes.json: base roles must appear exactly once"
                )
            if enhancement_count > 2:
                errors.append(
                    "research-axes.json: at most two enhancement axes are allowed"
                )
            missing_lanes = sorted(set(LANES) - covered_lanes)
            if missing_lanes:
                errors.append(
                    "research-axes.json: lane coverage missing "
                    + ", ".join(missing_lanes)
                )

    plan_rows = validate_jsonl(
        workspace / "exa-query-plan.jsonl",
        QUERY_PLAN_REQUIRED,
        errors,
        "exa-query-plan.jsonl",
    )
    execution_rows = validate_jsonl(
        workspace / "exa-query-execution.jsonl",
        QUERY_EXECUTION_REQUIRED,
        errors,
        "exa-query-execution.jsonl",
    )
    plan_by_id: dict[str, dict[str, Any]] = {}
    for row in plan_rows:
        query_id = str(row.get("query_id") or "")
        if not query_id:
            errors.append("exa-query-plan.jsonl: query_id cannot be empty")
            continue
        if query_id in plan_by_id:
            errors.append(
                f"exa-query-plan.jsonl: duplicate query_id {query_id}"
            )
        plan_by_id[query_id] = row
        if str(row.get("axis_id") or "") not in axis_ids:
            errors.append(
                f"exa-query-plan.jsonl: {query_id} references unknown axis "
                f"{row.get('axis_id')}"
            )

    executed_ids: set[str] = set()
    for row in execution_rows:
        query_id = str(row.get("query_id") or "")
        if query_id not in plan_by_id:
            errors.append(
                f"exa-query-execution.jsonl: unknown query_id {query_id}"
            )
            continue
        if query_id in executed_ids:
            errors.append(
                f"exa-query-execution.jsonl: duplicate query_id {query_id}"
            )
        executed_ids.add(query_id)
        if row.get("status") not in QUERY_EXECUTION_STATUSES:
            errors.append(
                f"exa-query-execution.jsonl: invalid status "
                f"{row.get('status')!r}"
            )
        plan_row = plan_by_id[query_id]
        for field in ("plan_id", "axis_id", "lane", "source_family", "exa_query"):
            if row.get(field) != plan_row.get(field):
                errors.append(
                    f"exa-query-execution.jsonl: {query_id} {field} "
                    "does not match query plan"
                )

    for row in exa_rows:
        query_id = str(row.get("query_id") or "")
        plan_row = plan_by_id.get(query_id)
        if not plan_row:
            errors.append(
                f"exa-candidates.jsonl: unknown query_id "
                f"{query_id or '<empty>'}"
            )
            continue
        field_pairs = (
            ("plan_id", "plan_id"),
            ("axis_id", "axis_id"),
            ("lane", "lane"),
            ("source_family_planned", "source_family"),
            ("exa_query", "exa_query"),
        )
        for candidate_field, plan_field in field_pairs:
            if row.get(candidate_field) != plan_row.get(plan_field):
                errors.append(
                    f"exa-candidates.jsonl: {query_id} {candidate_field} "
                    "does not match query plan"
                )

    missing_execution = sorted(set(plan_by_id) - executed_ids)
    if missing_execution:
        errors.append(
            "exa-query-execution.jsonl: planned queries not executed: "
            + ", ".join(missing_execution)
        )


def validate_standard_output_paths(workspace: Path, errors: list[str]) -> None:
    if workspace.parent.name != "runs" or not workspace.name.startswith("ai-mapper-"):
        return
    base = workspace.parents[1]
    match = re.match(r"ai-mapper-(\d{8})-", workspace.name)
    if not match:
        errors.append("workspace: name must contain ai-mapper-YYYYMMDD-HHMMSS for standard path validation")
        return
    mmdd = match.group(1)[4:]
    expected_paths = (
        base / f"{mmdd}-ai-mapper.md",
        base / "raw" / f"{mmdd}-ai-mapper-raw.md",
        base / "最新AI项目与人才Mapping.md",
    )
    for path in expected_paths:
        if not path.exists():
            errors.append(f"missing standard output path {path}")


def validate_workspace(workspace: Path, skill_dir: Path | None = None) -> list[str]:
    errors: list[str] = []
    skill_dir = skill_dir or Path(__file__).resolve().parents[1]
    run_modes = load_run_modes(skill_dir) if skill_dir else {}

    for rel in REQUIRED_WORKSPACE_FILES:
        exists(workspace / rel, errors, rel)
    for lane in LANES:
        validate_lane_file(workspace / "results" / f"{lane}.md", errors)

    exa_rows = validate_jsonl(workspace / "exa-candidates.jsonl", EXA_CANDIDATE_REQUIRED, errors, "exa-candidates.jsonl")
    candidate_rows = validate_jsonl(workspace / "candidates.jsonl", CANDIDATE_REQUIRED, errors, "candidates.jsonl")
    evidence_rows = validate_jsonl(workspace / "evidence.jsonl", EVIDENCE_REQUIRED, errors, "evidence.jsonl")
    validate_query_artifacts(workspace, exa_rows, errors)
    validate_structured_links(exa_rows, candidate_rows, evidence_rows, errors)
    validate_standard_output_paths(workspace, errors)

    report_text = read(workspace / "run-report.md") if (workspace / "run-report.md").exists() else ""
    final_text = read(workspace / "AI项目与人才Mapping.md") if (workspace / "AI项目与人才Mapping.md").exists() else ""
    degraded = "degraded / Exa-only" in report_text or "degraded / Exa-only" in final_text

    topics = workspace / "topics.md"
    if topics.exists():
        topics_text = read(topics)
        if degraded:
            if not any(term in topics_text for term in ("Elsewhere Keyword Intelligence", "Elsewhere API Unavailable", "Elsewhere unavailable", "待补 Elsewhere")):
                errors.append("topics.md: degraded runs must include Elsewhere unavailable/待补 Elsewhere status")
        else:
            require_text(topics_text, "Elsewhere Keyword Intelligence", errors, "topics.md")

    validated = workspace / "validated.md"
    if validated.exists():
        validated_text = read(validated)
        require_text(validated_text, "Elsewhere API discovery/supplement", errors, "validated.md")
        if degraded:
            if "source_origin=Elsewhere API" not in validated_text and "not run - Elsewhere unavailable" not in validated_text:
                errors.append("validated.md: degraded runs must mark Elsewhere supplement as not run - Elsewhere unavailable")
        else:
            require_text(validated_text, "source_origin=Elsewhere API", errors, "validated.md")
        require_text(validated_text, "人才类线索", errors, "validated.md")
        forbid_elsewhere_team_person_gap(validated_text, errors, "validated.md")

    rated = workspace / "rated.md"
    if rated.exists():
        rated_text = read(rated)
        require_text(rated_text, PROJECT_TABLE_HEADER, errors, "rated.md")
        require_text(rated_text, TALENT_TABLE_HEADER, errors, "rated.md")
        forbid_text(rated_text, "context-mode-only", errors, "rated.md")
        forbid_elsewhere_team_person_gap(rated_text, errors, "rated.md")
        for term in BANNED_RECRUITING_TERMS:
            forbid_text(rated_text, term, errors, "rated.md")
        forbid_recruiting_text(rated_text, errors, "rated.md")

    final = workspace / "AI项目与人才Mapping.md"
    if final.exists():
        if WEAK_DEGRADED_RE.search(final_text):
            errors.append("final report: use exact completeness `degraded / Exa-only`, not bare `degraded`")
        if not final_text.lstrip().startswith("## 运行状态"):
            errors.append("final report: must start with ## 运行状态")
        for needle in ("运行状态", "run_mode", PROJECT_TABLE_HEADER, TALENT_TABLE_HEADER, "来源质量复盘"):
            require_text(final_text, needle, errors, "final report")
        forbid_text(final_text, "触达建议", errors, "final report")
        forbid_elsewhere_team_person_gap(final_text, errors, "final report")
        forbid_recruiting_text(final_text, errors, "final report")

    report = workspace / "run-report.md"
    if report.exists():
        for needle in (
            "Elsewhere API 使用质量", "Exa 召回质量", "A 类项目审计", "真实日期审计",
            "Recall Volume Gate", "Exa Search Quantity Gate", "Source Coverage Gate",
            "Elsewhere Financing Pass", "Exa candidate audit", "Exa triage/open audit", "run_mode", "marginal-yield",
        ):
            require_text(report_text, needle, errors, "run-report.md")
        validate_gate_table(report_text, errors, run_modes)
        forbid_elsewhere_team_person_gap(report_text, errors, "run-report.md")
        expected_exa_candidates = gate_actual(report_text, "Total Exa candidate URLs")
        actual_exa_candidate_rows = non_status_jsonl_count(workspace / "exa-candidates.jsonl")
        if expected_exa_candidates is not None and actual_exa_candidate_rows is not None:
            if actual_exa_candidate_rows < expected_exa_candidates:
                errors.append(
                    "exa-candidates.jsonl: non-status row count "
                    f"{actual_exa_candidate_rows} below run-report Total Exa candidate URLs "
                    f"{expected_exa_candidates}"
                )
        expected_opened = gate_actual(report_text, "Total opened/fetched original pages")
        actual_opened = sum(1 for row in exa_rows if row.get("fetch_status") in {"opened", "fetched"})
        if expected_opened is not None and actual_opened < expected_opened:
            errors.append(
                "exa-candidates.jsonl: opened/fetched row count "
                f"{actual_opened} below run-report Total opened/fetched original pages {expected_opened}"
            )
        expected_c_funding_opened = gate_actual(report_text, "C-funding opened/fetched pages")
        actual_c_funding_opened = sum(
            1 for row in exa_rows if row.get("lane") == "C-funding" and row.get("fetch_status") in {"opened", "fetched"}
        )
        if expected_c_funding_opened is not None and actual_c_funding_opened < expected_c_funding_opened:
            errors.append(
                "exa-candidates.jsonl: C-funding opened/fetched row count "
                f"{actual_c_funding_opened} below run-report C-funding opened/fetched pages {expected_c_funding_opened}"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ai-mapper skill package or run artifacts.")
    parser.add_argument("--skill-dir", type=Path, help="Path to ai-mapper skill directory.")
    parser.add_argument("--workspace", type=Path, help="Path to an ai-mapper run workspace.")
    args = parser.parse_args()
    if not args.skill_dir and not args.workspace:
        parser.error("pass --skill-dir and/or --workspace")

    errors: list[str] = []
    if args.skill_dir:
        errors.extend(validate_skill_dir(args.skill_dir))
    if args.workspace:
        errors.extend(validate_workspace(args.workspace, args.skill_dir))

    if errors:
        print("ai-mapper validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("ai-mapper validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
