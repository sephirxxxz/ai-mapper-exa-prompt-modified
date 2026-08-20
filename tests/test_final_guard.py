from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

from ai_mapper_agent.evidence import read_jsonl, record_evidence, record_exa_response, record_fetch, record_query_attempt
from ai_mapper_agent.exa import build_search_payload
from ai_mapper_agent.guard import final_guard
from ai_mapper_agent.context_mode import (
    ContextIndexReceipt,
    ContextPreflightReceipt,
    record_context_index,
    record_context_preflight,
)
from ai_mapper_agent.run import create_run, finalize_run


NOW = datetime(2026, 8, 19, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai"))


def prepare_terminal_zero_result_run(root: Path):
    run = create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)
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
    (run.path / "candidate-cards.md").write_text("# 候选人\n\n本次无合格候选人。\n", encoding="utf-8")
    (run.path / "report.md").write_text("# AI Mapper 报告\n\n固定 40 次搜索已完成。\n", encoding="utf-8")
    (run.path / "run-report.md").write_text("# 运行报告\n\n流程完整完成。\n", encoding="utf-8")
    return finalize_run(run, status="complete", stop_code="SUCCESS", reason="all gates passed", impact="none")


class FinalGuardTests(unittest.TestCase):
    def test_guard_rejects_nonterminal_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = create_run(Path(temp), topic=None, timezone_name="Asia/Shanghai", now=NOW)

            result = final_guard(run.path)

            self.assertFalse(result.ok)
            self.assertIn("QUERY_NOT_TERMINAL", result.codes)

    def test_guard_rejects_failed_queries_as_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = create_run(Path(temp), topic=None, timezone_name="Asia/Shanghai", now=NOW)
            with (run.path / "query-execution.jsonl").open("a", encoding="utf-8") as handle:
                for index in range(1, 41):
                    handle.write(json.dumps({"query_id": f"q{index:02d}", "status": "failed"}) + "\n")
            manifest_path = run.path / "run-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["context_mode"] = {"status": "fresh_isolated", "project_dir": manifest["agent_root"], "context_dir": str(Path(manifest["agent_root"]) / ".context-mode"), "purge_scope": "project"}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertIn("QUERY_NOT_SUCCESSFUL", final_guard(run.path).codes)

    def test_guard_accepts_zero_candidates_when_process_gates_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))

            result = final_guard(run.path)

            self.assertTrue(result.ok, result.codes)

    def test_guard_requires_exa_results_to_be_indexed_into_context_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            events = read_jsonl(run.path / "events.jsonl")
            (run.path / "events.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in events if row.get("event") != "context_results_indexed"),
                encoding="utf-8",
            )

            result = final_guard(run.path)

            self.assertIn("CONTEXT_RESULTS_NOT_INDEXED", result.codes)

    def test_guard_rejects_more_than_sixty_fetched_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            for index in range(61):
                record_fetch(run, url=f"https://example.test/{index}", status="success", path=f"pages/p{index}.md")

            result = final_guard(run.path)

            self.assertFalse(result.ok)
            self.assertIn("FETCH_CAP_EXCEEDED", result.codes)

    def test_guard_rejects_a_tampered_fixed_query_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            rows = [json.loads(line) for line in (run.path / "query-plan.jsonl").read_text().splitlines()]
            rows[0]["query"] = "freehand replacement"
            (run.path / "query-plan.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            self.assertIn("QUERY_PLAN_TAMPERED", final_guard(run.path).codes)

    def test_guard_rejects_an_attempt_whose_request_does_not_match_the_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            planned = [json.loads(line) for line in (run.path / "query-plan.jsonl").read_text().splitlines()][0]
            forged = build_search_payload(planned)
            forged["query"] = "freehand replacement"
            (run.path / "query-attempts.jsonl").write_text(
                json.dumps({"query_id": "q01", "attempt": 1, "request": forged, "request_hash": "forged", "status": "success"}) + "\n",
                encoding="utf-8",
            )

            result = final_guard(run.path)

            self.assertFalse(result.ok)
            self.assertIn("EXA_REQUEST_PLAN_MISMATCH", result.codes)

    def test_guard_rejects_raw_results_missing_from_candidates_and_final_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            raw_rows = read_jsonl(run.path / "raw" / "exa-responses.jsonl")
            raw_rows[0]["response"]["results"] = [
                {"url": "https://public.test/project", "title": "Unrecorded project", "highlights": []}
            ]
            (run.path / "raw" / "exa-responses.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in raw_rows), encoding="utf-8"
            )

            result = final_guard(run.path)

            self.assertIn("RAW_RESULT_COUNT_MISMATCH", result.codes)
            self.assertIn("CANDIDATE_RESULT_MISMATCH", result.codes)

    def test_guard_rejects_a_or_b_candidate_claim_without_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            (run.path / "candidates.jsonl").write_text(
                json.dumps(
                    {
                        "candidate_id": "candidate_q01_001",
                        "duplicate_of": None,
                        "review_status": "reviewed",
                        "rating": "A",
                        "claims": [{"claim_id": "claim_launch", "text": "项目已发布", "evidence_ids": []}],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            result = final_guard(run.path)

            self.assertFalse(result.ok)
            self.assertIn("A_B_EVIDENCE_MISSING", result.codes)

    def test_guard_rejects_evidence_linked_from_another_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            page_body = "launch evidence"
            page = run.path / "pages" / "source.txt"
            page.write_text(page_body, encoding="utf-8")
            record_fetch(
                run,
                url="https://public.test/source",
                status="success",
                path="pages/source.txt",
                method="browser",
                byte_count=len(page_body.encode()),
                content_hash=__import__("hashlib").sha256(page_body.encode()).hexdigest(),
            )
            evidence = record_evidence(
                run,
                candidate_id="other",
                claim_id="other_claim",
                claim="other claim",
                source_url="https://public.test/source",
                fetched_at="2026-08-19T01:30:00+00:00",
                excerpt="launch evidence",
                page_content=page_body,
                verification_pattern=r"launch evidence",
            )
            candidates = [
                {
                    "candidate_id": "c1",
                    "duplicate_of": None,
                    "review_status": "reviewed",
                    "rating": "A",
                    "claims": [{"claim_id": "cl1", "text": "launched", "evidence_ids": [evidence["evidence_id"]]}],
                },
                {"candidate_id": "other", "duplicate_of": None, "review_status": "reviewed", "rating": "C", "claims": []},
            ]
            (run.path / "candidates.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in candidates), encoding="utf-8"
            )

            self.assertIn("CLAIM_EVIDENCE_MISMATCH", final_guard(run.path).codes)

    def test_guard_rejects_evidence_whose_claim_text_differs_from_candidate_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            page_body = "The project launched publicly."
            page = run.path / "pages" / "source.txt"
            page.write_text(page_body, encoding="utf-8")
            record_fetch(
                run,
                url="https://public.test/source",
                status="success",
                path="pages/source.txt",
                method="browser",
                byte_count=len(page_body.encode()),
                content_hash=__import__("hashlib").sha256(page_body.encode()).hexdigest(),
            )
            evidence = record_evidence(
                run,
                candidate_id="c1",
                claim_id="cl1",
                claim="The project launched publicly.",
                source_url="https://public.test/source",
                fetched_at="2026-08-19T01:30:00+00:00",
                excerpt=page_body,
                page_content=page_body,
                verification_pattern=r"launched publicly",
            )
            candidate = {
                "candidate_id": "c1",
                "canonical_url": "https://public.test/source",
                "duplicate_of": None,
                "review_status": "reviewed",
                "rating": "A",
                "claims": [{"claim_id": "cl1", "text": "The project raised $10m.", "evidence_ids": [evidence["evidence_id"]]}],
            }
            (run.path / "candidates.jsonl").write_text(json.dumps(candidate) + "\n", encoding="utf-8")

            self.assertIn("CLAIM_TEXT_MISMATCH", final_guard(run.path).codes)

    def test_guard_rejects_an_unknown_candidate_rating(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            candidate = {
                "candidate_id": "c1",
                "canonical_url": "https://public.test/source",
                "duplicate_of": None,
                "review_status": "reviewed",
                "rating": "Z",
                "claims": [],
            }
            (run.path / "candidates.jsonl").write_text(json.dumps(candidate) + "\n", encoding="utf-8")

            self.assertIn("RATING_INVALID", final_guard(run.path).codes)

    def test_guard_rejects_excerpt_and_regex_absent_from_saved_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = prepare_terminal_zero_result_run(Path(temp))
            page_body = "This page is about cats."
            content_hash = __import__("hashlib").sha256(page_body.encode()).hexdigest()
            page = run.path / "pages" / "cats.txt"
            page.write_text(page_body, encoding="utf-8")
            record_fetch(
                run,
                url="https://public.test/cats",
                status="success",
                path="pages/cats.txt",
                method="browser",
                byte_count=len(page_body.encode()),
                content_hash=content_hash,
            )
            evidence = {
                "evidence_id": "e_forged",
                "candidate_id": "c1",
                "claim_id": "cl1",
                "claim": "Project launched in 2026",
                "source_url": "https://public.test/cats",
                "fetched_at": "2026-08-19T01:30:00+00:00",
                "excerpt": "Project launched in 2026",
                "content_hash": content_hash,
                "verification_pattern": "launched in 2026",
                "verification_status": "regex_matched",
            }
            (run.path / "evidence.jsonl").write_text(json.dumps(evidence) + "\n", encoding="utf-8")
            candidate = {
                "candidate_id": "c1",
                "canonical_url": "https://public.test/cats",
                "duplicate_of": None,
                "review_status": "reviewed",
                "rating": "A",
                "claims": [{"claim_id": "cl1", "text": "Project launched in 2026", "evidence_ids": ["e_forged"]}],
            }
            (run.path / "candidates.jsonl").write_text(json.dumps(candidate) + "\n", encoding="utf-8")

            self.assertIn("REGEX_EVIDENCE_MISMATCH", final_guard(run.path).codes)


if __name__ == "__main__":
    unittest.main()
