#!/usr/bin/env python3
"""Compile agent-authored research axes into an auditable Exa query plan."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


LANES = ("A-dev", "B-content", "C-funding", "D-academic")
BASE_ROLE_LANES = {
    "developer-product": "A-dev",
    "product-market": "B-content",
    "funding-company": "C-funding",
    "academic-productization": "D-academic",
}
ALLOWED_CANDIDATE_TYPES = {
    "person",
    "project",
    "repo",
    "content",
    "event",
    "paper",
    "company",
    "founder",
}
BANNED_SEED_RE = re.compile(
    r"\b(?:19|20)\d{2}\b|招聘|岗位|hiring|jobs?|job\s*board",
    re.I,
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def _string_list(raw: object, field: str, axis_id: str) -> list[str]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{axis_id}: {field} must be a non-empty list")
    values = [str(value).strip() for value in raw]
    if any(not value for value in values):
        raise ValueError(f"{axis_id}: {field} contains an empty value")
    return values


def _validate_dates(payload: dict[str, Any]) -> tuple[str, str, str]:
    collection = date.fromisoformat(str(payload.get("collection_date") or ""))
    window = payload.get("priority_window")
    if not isinstance(window, dict):
        raise ValueError("priority_window must be an object")
    start = date.fromisoformat(str(window.get("start") or ""))
    end = date.fromisoformat(str(window.get("end") or ""))
    if end != collection:
        raise ValueError("priority_window.end must equal collection_date")
    if start != collection - timedelta(days=30):
        raise ValueError("priority_window.start must be 30 days before collection_date")
    return collection.isoformat(), start.isoformat(), end.isoformat()


def validate_axes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    axes = payload.get("axes")
    if not isinstance(axes, list) or not 4 <= len(axes) <= 6:
        raise ValueError("axes must contain between 4 and 6 items")
    if payload.get("topic") != "通用扫描":
        raise ValueError("topic must be 通用扫描")
    _validate_dates(payload)

    seen_ids: set[str] = set()
    covered_lanes: set[str] = set()
    seen_base_roles: list[str] = []
    validated: list[dict[str, Any]] = []
    required = {
        "axis_id",
        "axis_type",
        "base_role",
        "label",
        "ranking_question",
        "search_seed",
        "candidate_types",
        "evidence_targets",
        "lane_affinity",
        "weight",
        "exclusions",
    }

    for raw in axes:
        if not isinstance(raw, dict):
            raise ValueError("every axis must be an object")
        missing = sorted(required - raw.keys())
        if missing:
            raise ValueError(f"axis missing keys: {', '.join(missing)}")

        axis_id = str(raw["axis_id"]).strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,47}", axis_id):
            raise ValueError(f"invalid axis_id: {axis_id}")
        if axis_id in seen_ids:
            raise ValueError(f"duplicate axis_id: {axis_id}")
        seen_ids.add(axis_id)

        axis_type = str(raw["axis_type"])
        base_role = raw["base_role"]
        if axis_type == "base":
            role = str(base_role)
            if role not in BASE_ROLE_LANES:
                raise ValueError(f"{axis_id}: invalid base_role")
            seen_base_roles.append(role)
        elif axis_type == "enhancement":
            if base_role not in {None, ""}:
                raise ValueError(f"{axis_id}: enhancement base_role must be null")
        else:
            raise ValueError(f"{axis_id}: axis_type must be base or enhancement")

        ranking_question = str(raw["ranking_question"]).strip()
        if len(ranking_question) < 20:
            raise ValueError(f"{axis_id}: ranking_question is too short")
        search_seed = str(raw["search_seed"]).strip()
        if BANNED_SEED_RE.search(search_seed):
            raise ValueError(
                "search_seed must not contain dates or banned recruiting terms"
            )

        candidate_types = set(
            _string_list(raw["candidate_types"], "candidate_types", axis_id)
        )
        if not candidate_types <= ALLOWED_CANDIDATE_TYPES:
            raise ValueError(f"{axis_id}: invalid candidate_types")
        _string_list(raw["evidence_targets"], "evidence_targets", axis_id)
        _string_list(raw["exclusions"], "exclusions", axis_id)

        lane_affinity = set(
            _string_list(raw["lane_affinity"], "lane_affinity", axis_id)
        )
        if not lane_affinity <= set(LANES):
            raise ValueError(f"{axis_id}: invalid lane_affinity")
        if axis_type == "base" and BASE_ROLE_LANES[str(base_role)] not in lane_affinity:
            raise ValueError(
                f"{axis_id}: base role {base_role} must include "
                f"{BASE_ROLE_LANES[str(base_role)]}"
            )
        covered_lanes.update(lane_affinity)

        weight = float(raw["weight"])
        if not 0.1 <= weight <= 1.0:
            raise ValueError(f"{axis_id}: weight must be between 0.1 and 1.0")
        validated.append(raw)

    if sorted(seen_base_roles) != sorted(BASE_ROLE_LANES):
        raise ValueError(
            "base roles must appear exactly once: "
            + ", ".join(BASE_ROLE_LANES)
        )
    if len(axes) - len(seen_base_roles) > 2:
        raise ValueError("at most two enhancement axes are allowed")
    missing_lanes = sorted(set(LANES) - covered_lanes)
    if missing_lanes:
        raise ValueError(f"lane coverage missing: {', '.join(missing_lanes)}")
    return validated


def range_floor(value: object) -> int:
    match = re.match(r"(\d+)", str(value))
    if not match:
        raise ValueError(f"invalid query range: {value}")
    return int(match.group(1))


def lane_floors(
    run_modes: dict[str, Any],
    run_mode: str,
) -> dict[str, int]:
    try:
        mode = run_modes["modes"][run_mode]
    except KeyError as exc:
        raise ValueError(f"unknown run mode: {run_mode}") from exc
    floors = {
        lane: range_floor(mode["lane_targets"][lane]["queries"])
        for lane in LANES
    }
    funding_gate = int(
        mode["gates"]["C-funding query/source paths"]["minimum"]
    )
    floors["C-funding"] = max(floors["C-funding"], funding_gate)
    return floors


def normalize_query(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def compile_rows(
    payload: dict[str, Any],
    packs: dict[str, Any],
    run_modes: dict[str, Any],
    run_mode: str,
) -> list[dict[str, Any]]:
    axes = validate_axes(payload)
    floors = lane_floors(run_modes, run_mode)
    collection_date, window_start, window_end = _validate_dates(payload)
    year, month, _ = collection_date.split("-")
    plan_id = f"exa-plan-{collection_date}-{run_mode.replace(' ', '-')}"
    rows: list[dict[str, Any]] = []
    used_queries: set[str] = set()

    for lane in LANES:
        lane_axes = [axis for axis in axes if lane in axis["lane_affinity"]]
        lane_pack = packs["lanes"][lane]
        base_axes = [axis for axis in lane_axes if axis["axis_type"] == "base"]
        enhancement_axes = [
            axis for axis in lane_axes if axis["axis_type"] == "enhancement"
        ]

        def expand(
            selected_axes: list[dict[str, Any]],
        ) -> list[tuple[dict[str, Any], dict[str, str], str]]:
            candidates: list[tuple[dict[str, Any], dict[str, str], str]] = []
            for source in lane_pack["sources"]:
                for variant in lane_pack["variants"]:
                    for axis in sorted(
                        selected_axes,
                        key=lambda item: (
                            -float(item["weight"]),
                            str(item["axis_id"]),
                        ),
                    ):
                        candidates.append((axis, source, variant))
            return candidates

        lane_count = 0
        base_candidates = expand(base_axes)
        enhancement_candidates = expand(enhancement_axes)

        def append_candidates(
            candidates: list[tuple[dict[str, Any], dict[str, str], str]],
            limit: int,
        ) -> int:
            added = 0
            for axis, source, variant in candidates:
                query = normalize_query(
                    f'{source["prefix"]} {axis["search_seed"]} '
                    f"{variant} {year} {month}"
                )
                if query in used_queries:
                    continue
                used_queries.add(query)
                rows.append(
                    {
                        "schema_version": "1.0",
                        "plan_id": plan_id,
                        "query_id": f"q-{len(rows) + 1:04d}",
                        "axis_id": axis["axis_id"],
                        "lane": lane,
                        "source_family": source["family"],
                        "exa_query": query,
                        "ranking_question": axis["ranking_question"],
                        "candidate_types": axis["candidate_types"],
                        "evidence_targets": axis["evidence_targets"],
                        "priority": axis["weight"],
                        "run_mode": run_mode,
                        "collection_date": collection_date,
                        "priority_window_start": window_start,
                        "priority_window_end": window_end,
                        "execution_status": "planned",
                    }
                )
                added += 1
                if added >= limit:
                    break
            return added

        enhancement_quota = (
            max(1, floors[lane] // 5) if enhancement_candidates else 0
        )
        base_target = floors[lane] - enhancement_quota
        lane_count += append_candidates(base_candidates, base_target)
        lane_count += append_candidates(
            enhancement_candidates,
            enhancement_quota,
        )
        if lane_count < floors[lane]:
            lane_count += append_candidates(
                base_candidates + enhancement_candidates,
                floors[lane] - lane_count,
            )

        if lane_count < floors[lane]:
            raise ValueError(
                f"{lane}: source packs cannot satisfy query floor {floors[lane]}"
            )
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile AI Mapper research axes into an Exa query plan."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("--workspace", type=Path, required=True)
    compile_parser.add_argument(
        "--run-mode",
        choices=["adaptive standard scan", "deep map"],
        required=True,
    )
    args = parser.parse_args()

    try:
        skill_dir = Path(__file__).resolve().parents[1]
        payload = read_json(args.workspace / "research-axes.json")
        packs = read_json(skill_dir / "references" / "exa-query-packs.json")
        run_modes = read_json(skill_dir / "references" / "run-modes.json")
        rows = compile_rows(payload, packs, run_modes, args.run_mode)
        output = args.workspace / "exa-query-plan.jsonl"
        write_jsonl(output, rows)
        print(
            json.dumps(
                {"planned": len(rows), "path": str(output)},
                ensure_ascii=False,
            )
        )
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        print(f"EXA Query Plan compilation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
