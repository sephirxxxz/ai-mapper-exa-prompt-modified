from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

import ai_mapper_agent.evidence as evidence_module
from ai_mapper_agent.evidence import record_exa_response, record_evidence, read_jsonl
from ai_mapper_agent.run import create_run


NOW = datetime(2026, 8, 19, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
RESULT = {
    "title": "Example AI project",
    "url": "https://example.test/project",
    "publishedDate": "2026-08-10T12:00:00.000Z",
    "author": "Example author",
    "highlights": ["A routing hint only"],
}


class EvidencePipelineTests(unittest.TestCase):
    def test_every_exa_result_is_retained_and_duplicate_is_linked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = create_run(Path(temp), topic=None, timezone_name="Asia/Shanghai", now=NOW)
            record_exa_response(run, "q01", {"requestId": "r1", "results": [RESULT, {**RESULT, "url": "https://example.test/project/"}]})

            raw_rows = read_jsonl(run.path / "raw" / "exa-responses.jsonl")
            candidates = read_jsonl(run.path / "candidates.jsonl")
            execution = read_jsonl(run.path / "query-execution.jsonl")
            self.assertEqual(raw_rows[0]["query_id"], "q01")
            self.assertEqual(raw_rows[0]["response"]["results"], [RESULT, {**RESULT, "url": "https://example.test/project/"}])
            self.assertEqual(len(candidates), 2)
            self.assertIsNone(candidates[0]["duplicate_of"])
            self.assertEqual(candidates[1]["duplicate_of"], candidates[0]["candidate_id"])
            self.assertEqual(candidates[0]["review_status"], "pending")
            self.assertEqual(execution[0]["status"], "completed")
            self.assertEqual(execution[0]["result_count"], 2)

    def test_zero_result_response_is_a_legal_terminal_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = create_run(Path(temp), topic=None, timezone_name="Asia/Shanghai", now=NOW)
            record_exa_response(run, "q01", {"requestId": "r2", "results": []})

            execution = read_jsonl(run.path / "query-execution.jsonl")
            self.assertEqual(execution[0]["status"], "zero_results")
            self.assertEqual(execution[0]["result_count"], 0)

    def test_evidence_claim_contains_hash_excerpt_and_source_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = create_run(Path(temp), topic=None, timezone_name="Asia/Shanghai", now=NOW)
            evidence = record_evidence(
                run,
                candidate_id="candidate_q01_001",
                claim_id="claim_launch_date",
                claim="产品在 2026-08-10 发布。",
                source_url="https://example.test/project",
                fetched_at="2026-08-19T01:30:00+00:00",
                excerpt="We launched the project on August 10.",
                page_content="We launched the project on August 10.",
                verification_pattern=r"launched the project on August 10",
            )

            saved = read_jsonl(run.path / "evidence.jsonl")
            self.assertEqual(saved, [evidence])
            self.assertTrue(evidence["evidence_id"].startswith("e_"))
            self.assertEqual(evidence["claim_id"], "claim_launch_date")
            self.assertEqual(len(evidence["content_hash"]), 64)
            self.assertEqual(evidence["verification_status"], "regex_matched")

    def test_evidence_is_rejected_when_pattern_or_excerpt_is_not_on_the_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = create_run(Path(temp), topic=None, timezone_name="Asia/Shanghai", now=NOW)
            with self.assertRaisesRegex(ValueError, "verify"):
                record_evidence(
                    run,
                    candidate_id="candidate_q01_001",
                    claim_id="claim_funding",
                    claim="项目融资一千万美元。",
                    source_url="https://example.test/project",
                    fetched_at="2026-08-19T01:30:00+00:00",
                    excerpt="The company raised $10m.",
                    page_content="This page is about cats.",
                    verification_pattern=r"raised \$10m",
                )

    def test_claim_ids_are_stable_and_candidate_scoped(self) -> None:
        stable_claim_id = getattr(evidence_module, "stable_claim_id", None)
        self.assertTrue(callable(stable_claim_id), "stable_claim_id must exist")
        first = stable_claim_id("candidate_1", "产品已经发布")
        self.assertEqual(first, stable_claim_id("candidate_1", "产品已经发布"))
        self.assertNotEqual(first, stable_claim_id("candidate_2", "产品已经发布"))


if __name__ == "__main__":
    unittest.main()
