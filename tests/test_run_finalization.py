from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

from ai_mapper_agent.context_mode import ContextIndexReceipt, ContextPreflightReceipt, record_context_index, record_context_preflight
from ai_mapper_agent.evidence import read_jsonl, record_exa_response, record_query_attempt
from ai_mapper_agent.exa import build_search_payload
from ai_mapper_agent.guard import final_guard
import ai_mapper_agent.run as run_module


NOW = datetime(2026, 8, 19, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai"))


def prepare_run(root: Path, *, complete_queries: bool = True, reports: bool = False):
    run = run_module.create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)
    project_dir = run.manifest["agent_root"]
    record_context_preflight(
        run,
        ContextPreflightReceipt(
            doctor_tool="ctx_doctor",
            doctor_ok=True,
            doctor_summary="all required checks passed",
            purge_tool="ctx_purge",
            purge_ok=True,
            purge_scope="project",
            project_dir=project_dir,
            context_dir=str(Path(project_dir) / ".context-mode"),
            started_at="2026-08-19T01:29:00+00:00",
            completed_at="2026-08-19T01:29:02+00:00",
            host_call_ids=("doctor-call-1", "purge-call-1"),
        ),
    )
    if complete_queries:
        for row in read_jsonl(run.path / "query-plan.jsonl"):
            payload = build_search_payload(row)
            response = {"results": []}
            record_query_attempt(run, query_id=row["query_id"], attempt=1, request=payload, status="success", response=response)
            record_exa_response(run, row["query_id"], response, request=payload)
        record_context_index(
            run,
            ContextIndexReceipt(
                index_tool="ctx_index",
                index_ok=True,
                paths=("raw/exa-responses.jsonl", "candidates.jsonl"),
                indexed_at="2026-08-19T01:31:00+00:00",
                host_call_id="index-call-1",
            ),
        )
    if reports:
        (run.path / "candidate-cards.md").write_text("# 候选人\n\n本次无合格候选人。\n", encoding="utf-8")
        (run.path / "report.md").write_text("# AI Mapper 报告\n\n固定 40 次搜索已完成。\n", encoding="utf-8")
        (run.path / "run-report.md").write_text("# 运行报告\n\n流程完整完成。\n", encoding="utf-8")
    return run


class RunFinalizationTests(unittest.TestCase):
    def test_guard_rejects_empty_reports_and_in_progress_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_run(Path(temp), complete_queries=True, reports=False)

            result = final_guard(run.path)

            self.assertIn("RUN_NOT_FINALIZED", result.codes)
            self.assertIn("REPORT_EMPTY", result.codes)

    def test_complete_updates_both_pointers_only_after_guard(self) -> None:
        finalize = getattr(run_module, "finalize_run", None)
        self.assertTrue(callable(finalize), "finalize_run must exist")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = prepare_run(root, reports=True)
            self.assertFalse((root / "runs" / "latest.json").exists())

            finalized = finalize(
                run,
                status="complete",
                stop_code="SUCCESS",
                reason="all gates passed",
                impact="none",
            )

            latest = json.loads((root / "runs" / "latest.json").read_text())
            latest_complete = json.loads((root / "runs" / "latest-complete.json").read_text())
            self.assertEqual(latest["run_id"], run.run_id)
            self.assertEqual(latest_complete["run_id"], run.run_id)
            self.assertEqual(finalized.manifest["status"], "complete")
            self.assertTrue(final_guard(run.path).ok)

    def test_partial_never_moves_latest_complete(self) -> None:
        finalize = getattr(run_module, "finalize_run", None)
        self.assertTrue(callable(finalize), "finalize_run must exist")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = prepare_run(root, complete_queries=False, reports=True)

            finalized = finalize(
                run,
                status="partial",
                stop_code="EXA_CREDITS_EXHAUSTED",
                reason="Exa credits ended before all queries ran",
                impact="40 queries were not executed",
            )

            self.assertEqual(finalized.manifest["status"], "partial")
            self.assertEqual(json.loads((root / "runs" / "latest.json").read_text())["run_id"], run.run_id)
            self.assertFalse((root / "runs" / "latest-complete.json").exists())

    def test_finalized_run_cannot_transition_a_second_time(self) -> None:
        finalize = getattr(run_module, "finalize_run", None)
        self.assertTrue(callable(finalize), "finalize_run must exist")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = prepare_run(root, reports=True)
            complete = finalize(
                run,
                status="complete",
                stop_code="SUCCESS",
                reason="all gates passed",
                impact="none",
            )

            with self.assertRaisesRegex(ValueError, "already finalized"):
                finalize(
                    complete,
                    status="partial",
                    stop_code="LATE_CHANGE",
                    reason="attempted second transition",
                    impact="would corrupt latest pointers",
                )

            manifest = json.loads((run.path / "run-manifest.json").read_text())
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(json.loads((root / "runs" / "latest-complete.json").read_text())["run_id"], run.run_id)


if __name__ == "__main__":
    unittest.main()
