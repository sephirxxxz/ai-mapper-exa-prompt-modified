from __future__ import annotations

from datetime import datetime
import importlib
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

from ai_mapper_agent.guard import final_guard
from ai_mapper_agent.run import create_run, finalize_run


try:
    context_mode = importlib.import_module("ai_mapper_agent.context_mode")
except ModuleNotFoundError:
    context_mode = None


NOW = datetime(2026, 8, 19, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai"))


def valid_receipt(run):
    if context_mode is None:
        return None
    receipt_type = getattr(context_mode, "ContextPreflightReceipt", None)
    if not isinstance(receipt_type, type):
        return None
    root = str(Path(run.manifest["agent_root"]).resolve())
    return receipt_type(
        doctor_tool="ctx_doctor",
        doctor_ok=True,
        doctor_summary="all required checks passed",
        purge_tool="ctx_purge",
        purge_ok=True,
        purge_scope="project",
        project_dir=root,
        context_dir=str(Path(root) / ".context-mode"),
        started_at="2026-08-19T01:29:00+00:00",
        completed_at="2026-08-19T01:29:02+00:00",
        host_call_ids=("doctor-call-1", "purge-call-1"),
    )


class ContextModeReceiptTests(unittest.TestCase):
    def _run(self, root: Path):
        return create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)

    def test_plain_ok_strings_cannot_create_a_context_receipt(self) -> None:
        recorder = getattr(context_mode, "record_context_preflight", None) if context_mode else None
        self.assertTrue(callable(recorder), "record_context_preflight must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            with self.assertRaises(TypeError):
                recorder(run, doctor_result="OK", purge_result="OK")

    def test_receipt_must_use_the_exact_isolated_directories(self) -> None:
        recorder = getattr(context_mode, "record_context_preflight", None) if context_mode else None
        receipt_type = getattr(context_mode, "ContextPreflightReceipt", None) if context_mode else None
        self.assertTrue(callable(recorder) and isinstance(receipt_type, type), "structured receipt API must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            receipt = valid_receipt(run)
            bad = receipt_type(**{**receipt.__dict__, "context_dir": "/tmp/shared-context"})
            with self.assertRaisesRegex(ValueError, "context directory"):
                recorder(run, bad)

    def test_guard_rejects_context_preflight_after_research(self) -> None:
        recorder = getattr(context_mode, "record_context_preflight", None) if context_mode else None
        append_event = getattr(context_mode, "append_event", None) if context_mode else None
        self.assertTrue(callable(recorder) and callable(append_event), "context event API must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            append_event(run, {"event": "query_attempt", "query_id": "q01"})
            recorder(run, valid_receipt(run))

            self.assertIn("CONTEXT_MODE_ORDER", final_guard(run.path).codes)

    def test_guard_requires_exactly_one_fresh_run_project_purge(self) -> None:
        recorder = getattr(context_mode, "record_context_preflight", None) if context_mode else None
        self.assertTrue(callable(recorder), "record_context_preflight must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            receipt = valid_receipt(run)
            recorder(run, receipt)
            recorder(run, receipt)

            self.assertIn("CONTEXT_MODE_PURGE_COUNT", final_guard(run.path).codes)

    def test_failed_doctor_cannot_be_overwritten_by_a_successful_preflight(self) -> None:
        failure_type = getattr(context_mode, "ContextFailureReceipt", None) if context_mode else None
        failure_recorder = getattr(context_mode, "record_context_failure", None) if context_mode else None
        success_recorder = getattr(context_mode, "record_context_preflight", None) if context_mode else None
        self.assertTrue(
            isinstance(failure_type, type) and callable(failure_recorder) and callable(success_recorder),
            "Context receipt APIs must exist",
        )
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            root = run.manifest["agent_root"]
            failure_recorder(
                run,
                failure_type(
                    doctor_tool="ctx_doctor",
                    doctor_ok=False,
                    doctor_summary="ctx_doctor timed out",
                    project_dir=root,
                    context_dir=str(Path(root) / ".context-mode"),
                    started_at="2026-08-19T01:29:00+00:00",
                    completed_at="2026-08-19T01:29:30+00:00",
                    host_call_id="doctor-timeout-1",
                ),
            )

            with self.assertRaisesRegex(RuntimeError, "already failed"):
                success_recorder(run, valid_receipt(run))

            self.assertIn("CONTEXT_MODE_FAILURE_PATH_INVALID", final_guard(run.path).codes)

    def test_doctor_failure_can_finalize_a_nonresearch_run_as_blocked(self) -> None:
        failure_type = getattr(context_mode, "ContextFailureReceipt", None) if context_mode else None
        recorder = getattr(context_mode, "record_context_failure", None) if context_mode else None
        self.assertTrue(isinstance(failure_type, type) and callable(recorder), "Context failure receipt API must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            root = run.manifest["agent_root"]
            recorder(
                run,
                failure_type(
                    doctor_tool="ctx_doctor",
                    doctor_ok=False,
                    doctor_summary="ctx_doctor timed out",
                    project_dir=root,
                    context_dir=str(Path(root) / ".context-mode"),
                    started_at="2026-08-19T01:29:00+00:00",
                    completed_at="2026-08-19T01:29:30+00:00",
                    host_call_id="doctor-timeout-1",
                ),
            )
            for name in ("candidate-cards.md", "report.md", "run-report.md"):
                (run.path / name).write_text("# Blocked\n\nContext Mode diagnostics timed out.\n", encoding="utf-8")

            finalized = finalize_run(
                run,
                status="blocked",
                stop_code="CONTEXT_MODE_UNAVAILABLE",
                reason="ctx_doctor timed out",
                impact="No search, fetch, or synthesis was performed",
            )

            self.assertEqual(finalized.manifest["status"], "blocked")
            self.assertTrue(final_guard(run.path).ok)


if __name__ == "__main__":
    unittest.main()
