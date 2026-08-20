from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

from ai_mapper_agent.run import create_run, resume_run


NOW = datetime(2026, 8, 19, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai"))


class RunLifecycleTests(unittest.TestCase):
    def test_new_run_writes_manifest_query_plan_and_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)

            self.assertEqual(run.manifest["status"], "in_progress")
            self.assertEqual(run.manifest["schema_version"], 2)
            self.assertEqual(run.manifest["query_count"], 40)
            self.assertTrue((run.path / "raw" / "exa-responses.jsonl").is_file())
            self.assertTrue((run.path / "query-plan.jsonl").is_file())
            self.assertTrue((run.path / "events.jsonl").is_file())
            self.assertTrue((run.path / "candidate-cards.md").is_file())
            self.assertTrue((run.path / "report.md").is_file())
            self.assertTrue((run.path / "run-report.md").is_file())

            rows = [json.loads(line) for line in (run.path / "query-plan.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 40)

    def test_same_day_resume_returns_the_existing_run_without_creating_another(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = create_run(root, topic="AI agent", timezone_name="Asia/Shanghai", now=NOW)
            resumed = resume_run(root, created.run_id, now=NOW + timedelta(hours=3))

            self.assertEqual(resumed.run_id, created.run_id)
            self.assertEqual(len([path for path in (root / "runs").iterdir() if path.is_dir()]), 1)

    def test_cross_day_resume_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)

            with self.assertRaisesRegex(ValueError, "cross-day"):
                resume_run(root, created.run_id, now=NOW + timedelta(days=1))

    def test_run_records_local_and_utc_start_times(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = create_run(Path(temp), topic=None, timezone_name="Asia/Shanghai", now=NOW)

            self.assertEqual(run.manifest["started_at_local"], "2026-08-19T09:30:00+08:00")
            self.assertEqual(run.manifest["started_at_utc"], "2026-08-19T01:30:00+00:00")

    def test_run_creates_exact_root_marker_and_rejects_a_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)
            self.assertEqual((root / ".ai-mapper-project").read_text(encoding="utf-8").strip(), str(root.resolve()))

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".ai-mapper-project").write_text("/other/root\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "marker"):
                create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)

    def test_invalid_timezone_is_reported_as_a_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "unknown timezone"):
                create_run(Path(temp), topic=None, timezone_name="Mars/Olympus", now=NOW)

    def test_same_second_runs_receive_distinct_run_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)
            second = create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)

            self.assertNotEqual(second.run_id, first.run_id)
            self.assertEqual(second.run_id, f"{first.run_id}-02")

    def test_manifest_artifact_paths_are_relative_to_the_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = create_run(Path(temp), topic=None, timezone_name="Asia/Shanghai", now=NOW)

            self.assertEqual(run.manifest["artifacts"]["events.jsonl"], "events.jsonl")
            self.assertEqual(run.manifest["artifacts"]["raw/exa-responses.jsonl"], "raw/exa-responses.jsonl")
            self.assertTrue(all(not Path(value).is_absolute() for value in run.manifest["artifacts"].values()))


if __name__ == "__main__":
    unittest.main()
