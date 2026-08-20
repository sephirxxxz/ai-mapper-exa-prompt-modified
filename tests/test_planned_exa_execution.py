from __future__ import annotations

from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

import ai_mapper_agent.exa as exa
from ai_mapper_agent.context_mode import ContextPreflightReceipt, record_context_preflight
from ai_mapper_agent.evidence import read_jsonl
from ai_mapper_agent.run import create_run


NOW = datetime(2026, 8, 19, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai"))


class FakeTransport:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[dict] = []

    def post(self, url: str, payload: dict, *, timeout: float) -> dict:
        self.requests.append(payload)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        assert isinstance(outcome, dict)
        return outcome


class PlannedExaExecutionTests(unittest.TestCase):
    def _run(self, root: Path, *, preflight: bool = True):
        run = create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)
        if preflight:
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
        return run

    def test_run_has_a_dedicated_attempt_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            self.assertTrue((run.path / "query-attempts.jsonl").is_file())

    def test_execute_query_loads_payload_from_saved_plan(self) -> None:
        execute = getattr(exa, "execute_query", None)
        self.assertTrue(callable(execute), "execute_query must be the only public execution entry point")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            transport = FakeTransport([{"requestId": "r1", "results": []}])

            execute(run, "q01", transport=transport)

            planned = read_jsonl(run.path / "query-plan.jsonl")[0]
            self.assertEqual(transport.requests, [exa.build_search_payload(planned)])

    def test_public_execution_api_rejects_a_freehand_row(self) -> None:
        execute = getattr(exa, "execute_query", None)
        self.assertTrue(callable(execute), "execute_query must be available")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            with self.assertRaises(TypeError):
                execute(run, {"query": "freehand"}, transport=FakeTransport([]))

    def test_execution_is_blocked_until_context_preflight_is_recorded(self) -> None:
        execute = getattr(exa, "execute_query", None)
        self.assertTrue(callable(execute), "execute_query must be available")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp), preflight=False)
            transport = FakeTransport([{"results": []}])

            with self.assertRaisesRegex(RuntimeError, "Context Mode preflight"):
                execute(run, "q01", transport=transport)
            self.assertEqual(transport.requests, [])

    def test_transient_failures_create_three_attempts_but_one_final_status(self) -> None:
        execute = getattr(exa, "execute_query", None)
        error_type = getattr(exa, "TransientExaError", None)
        self.assertTrue(callable(execute), "execute_query must be available")
        self.assertTrue(isinstance(error_type, type), "TransientExaError must be available")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            transport = FakeTransport(
                [
                    error_type("temporarily unavailable", code="HTTP_503"),
                    error_type("rate limited", code="HTTP_429"),
                    {"requestId": "r3", "results": []},
                ]
            )

            execute(run, "q01", transport=transport, sleeper=lambda _: None)

            attempts = read_jsonl(run.path / "query-attempts.jsonl")
            final_rows = read_jsonl(run.path / "query-execution.jsonl")
            self.assertEqual([row["attempt"] for row in attempts], [1, 2, 3])
            self.assertEqual([row["status"] for row in attempts], ["transient_error", "transient_error", "success"])
            self.assertEqual(len(final_rows), 1)
            self.assertEqual(final_rows[0]["status"], "zero_results")
            self.assertEqual(final_rows[0]["final_attempt"], 3)

    def test_completed_query_is_rejected_before_a_second_network_call(self) -> None:
        execute = getattr(exa, "execute_query", None)
        self.assertTrue(callable(execute), "execute_query must be available")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            transport = FakeTransport([{"results": []}, {"results": []}])
            execute(run, "q01", transport=transport)

            with self.assertRaisesRegex(RuntimeError, "already finalized"):
                execute(run, "q01", transport=transport)

            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(len(read_jsonl(run.path / "query-attempts.jsonl")), 1)

    def test_malformed_success_response_gets_a_terminal_failure_without_raw_candidates(self) -> None:
        execute = getattr(exa, "execute_query", None)
        error_type = getattr(exa, "ExaError", None)
        self.assertTrue(callable(execute) and isinstance(error_type, type), "Exa execution errors must be available")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            with self.assertRaisesRegex(error_type, "results"):
                execute(run, "q01", transport=FakeTransport([{"requestId": "bad", "results": "not-a-list"}]))

            attempts = read_jsonl(run.path / "query-attempts.jsonl")
            finals = read_jsonl(run.path / "query-execution.jsonl")
            self.assertEqual(attempts[0]["status"], "error")
            self.assertEqual(attempts[0]["error_code"], "INVALID_RESPONSE")
            self.assertEqual(len(finals), 1)
            self.assertEqual(finals[0]["status"], "failed")
            self.assertEqual(finals[0]["error_code"], "INVALID_RESPONSE")
            self.assertEqual(read_jsonl(run.path / "raw" / "exa-responses.jsonl"), [])


if __name__ == "__main__":
    unittest.main()
