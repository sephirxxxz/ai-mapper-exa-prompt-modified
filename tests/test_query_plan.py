from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "build_exa_query_plan.py"
LANES = ("A-dev", "B-content", "C-funding", "D-academic")
BASE_ROLES = (
    "developer-product",
    "product-market",
    "funding-company",
    "academic-productization",
)


def base_axis(base_role: str, lane: str) -> dict[str, object]:
    return {
        "axis_id": base_role,
        "axis_type": "base",
        "base_role": base_role,
        "label": base_role.replace("-", " "),
        "ranking_question": (
            f"Find early China-relevant AI software candidates for {base_role} "
            "with an openable original source and a verifiable recent event."
        ),
        "search_seed": f"China AI software {base_role}",
        "candidate_types": ["project", "person"],
        "evidence_targets": ["true event date", "product proof"],
        "lane_affinity": [lane],
        "weight": 1.0,
        "exclusions": ["mature company", "B-round-or-later", "recruitment-only"],
    }


def canonical_axes() -> list[dict[str, object]]:
    return [
        base_axis(role, lane)
        for role, lane in zip(BASE_ROLES, LANES, strict=True)
    ]


def write_axes(workspace: Path, axes: list[dict[str, object]]) -> None:
    payload = {
        "schema_version": "1.0",
        "topic": "通用扫描",
        "objective": "发现中国相关早期 AI 软件项目与人才",
        "collection_date": "2026-07-09",
        "priority_window": {"start": "2026-06-09", "end": "2026-07-09"},
        "axes": axes,
    }
    (workspace / "research-axes.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_compile(
    workspace: Path,
    mode: str = "adaptive standard scan",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "compile",
            "--workspace",
            str(workspace),
            "--run-mode",
            mode,
        ],
        text=True,
        capture_output=True,
        check=False,
    )


class QueryPlanTests(unittest.TestCase):
    def test_rejects_fewer_than_four_or_more_than_six_axes(self) -> None:
        too_few = canonical_axes()[:3]
        too_many = canonical_axes() + [
            {
                **base_axis("developer-product", "A-dev"),
                "axis_id": f"enhancement-{index}",
                "axis_type": "enhancement",
                "base_role": None,
            }
            for index in range(3)
        ]
        for axes in (too_few, too_many):
            with self.subTest(axis_count=len(axes)), tempfile.TemporaryDirectory() as tmp:
                workspace = Path(tmp)
                write_axes(workspace, axes)
                result = run_compile(workspace)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("axes must contain between 4 and 6 items", result.stderr)

    def test_requires_each_mandatory_base_role_exactly_once(self) -> None:
        axes = canonical_axes()
        axes[-1] = {
            **axes[-1],
            "axis_id": "duplicate-funding",
            "base_role": "funding-company",
            "lane_affinity": ["C-funding"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            write_axes(workspace, axes)
            result = run_compile(workspace)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("base roles must appear exactly once", result.stderr)

    def test_standard_plan_meets_lane_floors_and_is_traceable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            write_axes(workspace, canonical_axes())
            result = run_compile(workspace)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [
                json.loads(line)
                for line in (workspace / "exa-query-plan.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            counts = {
                lane: sum(row["lane"] == lane for row in rows)
                for lane in LANES
            }
            self.assertGreaterEqual(counts["A-dev"], 10)
            self.assertGreaterEqual(counts["B-content"], 8)
            self.assertGreaterEqual(counts["C-funding"], 14)
            self.assertGreaterEqual(counts["D-academic"], 8)
            self.assertGreaterEqual(len(rows), 40)
            self.assertEqual(len({row["query_id"] for row in rows}), len(rows))
            self.assertEqual(len({row["exa_query"] for row in rows}), len(rows))
            self.assertTrue(all(row["axis_id"] for row in rows))
            self.assertTrue(all(row["ranking_question"] for row in rows))
            self.assertTrue(all(row["source_family"] for row in rows))

    def test_deep_plan_meets_deep_lane_floors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            write_axes(workspace, canonical_axes())
            result = run_compile(workspace, "deep map")
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [
                json.loads(line)
                for line in (workspace / "exa-query-plan.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            counts = {
                lane: sum(row["lane"] == lane for row in rows)
                for lane in LANES
            }
            self.assertGreaterEqual(counts["A-dev"], 25)
            self.assertGreaterEqual(counts["B-content"], 20)
            self.assertGreaterEqual(counts["C-funding"], 50)
            self.assertGreaterEqual(counts["D-academic"], 20)
            self.assertGreaterEqual(len(rows), 115)

    def test_rejects_stale_dates_and_recruiting_terms_in_agent_seed(self) -> None:
        axes = canonical_axes()
        axes[0] = {**axes[0], "search_seed": "China AI hiring jobs 2025"}
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            write_axes(workspace, axes)
            result = run_compile(workspace)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "search_seed must not contain dates or banned recruiting terms",
                result.stderr,
            )

    def test_enhancement_axis_receives_bounded_query_budget(self) -> None:
        axes = canonical_axes()
        axes.append(
            {
                **base_axis("developer-product", "A-dev"),
                "axis_id": "agent-security",
                "axis_type": "enhancement",
                "base_role": None,
                "label": "Agent security",
                "ranking_question": (
                    "Find early China-relevant AI agent security projects with "
                    "an openable original source and a verifiable recent event."
                ),
                "search_seed": "China AI agent security prompt injection",
                "weight": 0.8,
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            write_axes(workspace, axes)
            result = run_compile(workspace)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [
                json.loads(line)
                for line in (workspace / "exa-query-plan.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            enhancement_rows = [
                row for row in rows if row["axis_id"] == "agent-security"
            ]
            self.assertGreaterEqual(len(enhancement_rows), 1)
            self.assertLessEqual(len(enhancement_rows), 2)


if __name__ == "__main__":
    unittest.main()
