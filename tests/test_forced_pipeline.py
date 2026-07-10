from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "ai_mapper_forced_pipeline.py"
if not SCRIPT.exists():
    SCRIPT = ROOT.parent / "scripts" / "forced_pipeline.py"


def run_cli(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def write_query_plan(workspace: Path) -> Path:
    path = workspace / "exa-query-plan.jsonl"
    rows = [
        {
            "schema_version": "1.0",
            "plan_id": "exa-plan-2026-07-09-adaptive-standard-scan",
            "query_id": "q-0001",
            "axis_id": "developer-product",
            "lane": "A-dev",
            "source_family": "GitHub",
            "exa_query": "site:github.com China AI software release 2026 07",
            "ranking_question": "Find an early China-relevant AI software release with original evidence.",
            "candidate_types": ["project", "repo"],
            "evidence_targets": ["true event date", "repo"],
            "priority": 1.0,
            "run_mode": "adaptive standard scan",
            "collection_date": "2026-07-09",
            "priority_window_start": "2026-06-09",
            "priority_window_end": "2026-07-09",
            "execution_status": "planned",
        }
    ]
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    return path


class ForcedPipelineTests(unittest.TestCase):
    def test_record_exa_response_persists_every_returned_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            query_plan = write_query_plan(workspace)
            response = workspace / "exa-response.json"
            response.write_text(
                json.dumps(
                    {
                        "results": [
                            {"url": "https://github.com/example/a", "title": "A", "publishedDate": "2026-07-01"},
                            {"url": "https://36kr.com/p/1", "title": "B", "publishedDate": "2026-07-02"},
                            {"url": "https://openreview.net/forum?id=x", "title": "C", "publishedDate": "2026-07-03"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            run_cli(
                "record-exa-response",
                "--workspace",
                str(workspace),
                "--query-plan-file",
                str(query_plan),
                "--query-id",
                "q-0001",
                "--response-file",
                str(response),
                "--collection-date",
                "2026-07-09",
            )

            rows = [
                json.loads(line)
                for line in (workspace / "exa-candidates.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 3)
            self.assertEqual([row["returned_rank"] for row in rows], [1, 2, 3])
            self.assertTrue(all(row["fetch_status"] == "pending" for row in rows))
            self.assertTrue(all(row["query_id"] == "q-0001" for row in rows))
            self.assertTrue(
                all(row["axis_id"] == "developer-product" for row in rows)
            )
            executions = [
                json.loads(line)
                for line in (workspace / "exa-query-execution.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual(len(executions), 1)
            self.assertEqual(executions[0]["status"], "completed")
            self.assertEqual(executions[0]["result_count"], 3)

    def test_record_exa_response_records_zero_result_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            query_plan = write_query_plan(workspace)
            response = workspace / "exa-response.json"
            response.write_text('{"results": []}', encoding="utf-8")

            run_cli(
                "record-exa-response",
                "--workspace",
                str(workspace),
                "--query-plan-file",
                str(query_plan),
                "--query-id",
                "q-0001",
                "--response-file",
                str(response),
                "--collection-date",
                "2026-07-09",
            )

            self.assertEqual(
                (workspace / "exa-candidates.jsonl").read_text(encoding="utf-8"),
                "",
            )
            executions = [
                json.loads(line)
                for line in (workspace / "exa-query-execution.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual(executions[0]["status"], "queried_no_usable_result")
            self.assertEqual(executions[0]["result_count"], 0)

    def test_record_exa_response_rejects_unknown_query_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            query_plan = write_query_plan(workspace)
            response = workspace / "exa-response.json"
            response.write_text('{"results": []}', encoding="utf-8")

            result = run_cli(
                "record-exa-response",
                "--workspace",
                str(workspace),
                "--query-plan-file",
                str(query_plan),
                "--query-id",
                "q-9999",
                "--response-file",
                str(response),
                "--collection-date",
                "2026-07-09",
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown query_id", result.stderr)

    def test_guard_final_rejects_unexecuted_planned_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            write_query_plan(workspace)
            (workspace / "exa-candidates.jsonl").write_text("", encoding="utf-8")
            (workspace / "exa-query-execution.jsonl").write_text("", encoding="utf-8")
            (workspace / "candidates.jsonl").write_text("", encoding="utf-8")
            (workspace / "evidence.jsonl").write_text("", encoding="utf-8")

            result = run_cli(
                "guard-final",
                "--workspace",
                str(workspace),
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("planned Exa queries not executed: q-0001", result.stderr)

    def test_guard_final_fails_closed_when_standard_gates_are_under_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "exa-candidates.jsonl").write_text("", encoding="utf-8")
            (workspace / "candidates.jsonl").write_text("", encoding="utf-8")
            (workspace / "evidence.jsonl").write_text("", encoding="utf-8")

            result = run_cli("guard-final", "--workspace", str(workspace), check=False)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbids final/latest output", result.stderr)
            self.assertIn("not a valid blocked deliverable", result.stderr)
            self.assertIn("continue Exa recall", result.stderr)
            self.assertIn("Total Exa candidate URLs", result.stderr)
            self.assertIn("minimum 160", result.stderr)

    def test_elsewhere_available_requires_endpoint_coverage_not_just_five_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "exa-candidates.jsonl").write_text("", encoding="utf-8")
            (workspace / "evidence.jsonl").write_text("", encoding="utf-8")
            (workspace / "elsewhere-api-audit.jsonl").write_text(
                json.dumps({"endpoint_group": "search_chunks", "query": "AI Agent 融资"}) + "\n",
                encoding="utf-8",
            )
            candidates = []
            for i in range(5):
                candidates.append(
                    {
                        "candidate_id": f"els_{i}",
                        "name": f"Elsewhere candidate {i}",
                        "entry_type": "project",
                        "lane": "Elsewhere API discovery/supplement",
                        "source_origin": "Elsewhere API",
                        "run_mode": "adaptive standard scan",
                        "status": "validated",
                        "rating": "B / 继续观察",
                        "gap_type": "Evidence",
                        "evidence_ids": [],
                        "notes": "fact",
                    }
                )
            (workspace / "candidates.jsonl").write_text(
                "\n".join(json.dumps(row, ensure_ascii=False) for row in candidates) + "\n",
                encoding="utf-8",
            )

            result = run_cli("guard-final", "--workspace", str(workspace), "--elsewhere-status", "available", check=False)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Elsewhere endpoint coverage", result.stderr)
            self.assertIn("content_detail", result.stderr)


if __name__ == "__main__":
    unittest.main()
