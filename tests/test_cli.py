from __future__ import annotations

import json
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "exa-zero-results.json"


def run_cli(
    *arguments: str,
    test_mode: bool = False,
    cwd: Path = PROJECT_ROOT,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    if test_mode:
        environment["AI_MAPPER_TEST_MODE"] = "1"
    else:
        environment.pop("AI_MAPPER_TEST_MODE", None)
    if "--root" in arguments:
        root = Path(arguments[arguments.index("--root") + 1]).resolve()
        environment.setdefault("CONTEXT_MODE_PROJECT_DIR", str(root))
        environment.setdefault("CONTEXT_MODE_DIR", str(root / ".context-mode"))
    if env_overrides:
        environment.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "ai_mapper_agent", *arguments],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


class CliTests(unittest.TestCase):
    def test_cli_help_lists_supported_workflow_commands(self) -> None:
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in (
            "create",
            "context-record",
            "execute-query",
            "context-index-record",
            "fetch",
            "record-browser-fetch",
            "review-candidate",
            "record-evidence",
            "guard",
            "finalize",
        ):
            self.assertIn(command, result.stdout)

    def test_cli_exposes_real_candidate_workflow_operations(self) -> None:
        for command in ("fetch", "review-candidate", "record-evidence"):
            with self.subTest(command=command):
                result = run_cli(command, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_fixture_workflow_reaches_complete_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = run_cli(
                "create",
                "--root",
                str(root),
                "--timezone",
                "Asia/Shanghai",
                "--now",
                "2026-08-19T09:30:00+08:00",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_id = json.loads(created.stdout)["run_id"]

            context = run_cli(
                "context-record",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--doctor-call-id",
                "fixture-doctor-call",
                "--purge-call-id",
                "fixture-purge-call",
                "--doctor-summary",
                "all required checks passed",
                "--started-at",
                "2026-08-19T01:29:00+00:00",
                "--completed-at",
                "2026-08-19T01:29:02+00:00",
            )
            self.assertEqual(context.returncode, 0, context.stderr)

            for index in range(1, 41):
                executed = run_cli(
                    "execute-query",
                    "--root",
                    str(root),
                    "--run-id",
                    run_id,
                    "--query-id",
                    f"q{index:02d}",
                    "--fixture-response",
                    str(FIXTURE),
                    test_mode=True,
                )
                self.assertEqual(executed.returncode, 0, executed.stderr)

            indexed = run_cli(
                "context-index-record",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--host-call-id",
                "fixture-index-call",
                "--indexed-at",
                "2026-08-19T01:31:00+00:00",
            )
            self.assertEqual(indexed.returncode, 0, indexed.stderr)

            run_path = root / "runs" / run_id
            (run_path / "candidate-cards.md").write_text("# 候选人\n\n本次无合格候选人。\n", encoding="utf-8")
            (run_path / "report.md").write_text("# AI Mapper 报告\n\n固定 40 次搜索已完成。\n", encoding="utf-8")
            (run_path / "run-report.md").write_text("# 运行报告\n\n离线 fixture 流程完整完成。\n", encoding="utf-8")

            finalized = run_cli(
                "finalize",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--status",
                "complete",
                "--stop-code",
                "SUCCESS",
                "--reason",
                "all gates passed",
                "--impact",
                "none",
                test_mode=True,
            )
            self.assertEqual(finalized.returncode, 0, finalized.stderr)
            manifest = json.loads((run_path / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "complete")
            self.assertTrue(manifest["test_mode"])
            self.assertFalse((root / "runs" / "latest-complete.json").exists())
            production_guard = run_cli("guard", "--root", str(root), "--run-id", run_id)
            self.assertEqual(production_guard.returncode, 3)
            self.assertIn("TEST_MODE_RUN", production_guard.stdout)

    def test_fixture_flag_is_unavailable_in_production_mode(self) -> None:
        result = run_cli(
            "execute-query",
            "--root",
            "/tmp/unused",
            "--run-id",
            "unused",
            "--query-id",
            "q01",
            "--fixture-response",
            str(FIXTURE),
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_candidate_review_and_evidence_commands_update_one_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = run_cli(
                "create",
                "--root",
                str(root),
                "--timezone",
                "Asia/Shanghai",
                "--now",
                "2026-08-19T09:30:00+08:00",
            )
            run_id = json.loads(created.stdout)["run_id"]
            context = run_cli(
                "context-record",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--doctor-call-id",
                "doctor",
                "--purge-call-id",
                "purge",
                "--doctor-summary",
                "all checks passed",
                "--started-at",
                "2026-08-19T01:29:00+00:00",
                "--completed-at",
                "2026-08-19T01:29:02+00:00",
            )
            self.assertEqual(context.returncode, 0, context.stderr)
            run_path = root / "runs" / run_id
            candidate_id = "candidate_q01_a1_001"
            (run_path / "candidates.jsonl").write_text(
                json.dumps(
                    {
                        "candidate_id": candidate_id,
                        "query_id": "q01",
                        "returned_rank": 1,
                        "canonical_url": "https://public.test/project",
                        "url": "https://public.test/project",
                        "duplicate_of": None,
                        "review_status": "pending",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            body = "The project launched publicly."
            (run_path / "pages" / "source.txt").write_text(body, encoding="utf-8")
            (run_path / "fetches.jsonl").write_text(
                json.dumps(
                    {
                        "url": "https://public.test/source",
                        "method": "browser",
                        "status": "success",
                        "path": "pages/source.txt",
                        "byte_count": len(body.encode()),
                        "content_hash": sha256(body.encode()).hexdigest(),
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            reviewed = run_cli(
                "review-candidate",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--candidate-id",
                candidate_id,
                "--rating",
                "A",
                "--claims-json",
                '[{"claim_id":"cl1","text":"The project launched publicly.","evidence_ids":[]}]',
            )
            self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
            evidence = run_cli(
                "record-evidence",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--candidate-id",
                candidate_id,
                "--claim-id",
                "cl1",
                "--claim",
                "The project launched publicly.",
                "--source-url",
                "https://public.test/source",
                "--fetched-at",
                "2026-08-19T01:30:00+00:00",
                "--page",
                "pages/source.txt",
                "--excerpt",
                body,
                "--pattern",
                "launched publicly",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            saved_candidate = json.loads((run_path / "candidates.jsonl").read_text(encoding="utf-8"))
            self.assertTrue(saved_candidate["claims"][0]["evidence_ids"])

    def test_context_record_rejects_a_mismatched_context_mode_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = run_cli(
                "create",
                "--root",
                str(root),
                "--timezone",
                "Asia/Shanghai",
                "--now",
                "2026-08-19T09:30:00+08:00",
            )
            run_id = json.loads(created.stdout)["run_id"]
            context = run_cli(
                "context-record",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--doctor-call-id",
                "doctor",
                "--purge-call-id",
                "purge",
                "--doctor-summary",
                "all checks passed",
                "--started-at",
                "2026-08-19T01:29:00+00:00",
                "--completed-at",
                "2026-08-19T01:29:02+00:00",
                env_overrides={"CONTEXT_MODE_PROJECT_DIR": str(root / "wrong")},
            )
            self.assertEqual(context.returncode, 2)
            self.assertIn("CONTEXT_MODE", context.stderr)

    def test_candidate_bearing_fixture_workflow_reaches_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = root / "exa-one-result.json"
            fixture.write_text(
                json.dumps(
                    {
                        "requestId": "fixture-one-result",
                        "results": [
                            {
                                "url": "https://8.8.8.8/project",
                                "title": "Example AI project",
                                "publishedDate": "2026-08-18T12:00:00.000Z",
                                "highlights": ["The project launched publicly."],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            created = run_cli(
                "create",
                "--root",
                str(root),
                "--timezone",
                "Asia/Shanghai",
                "--now",
                "2026-08-19T09:30:00+08:00",
            )
            run_id = json.loads(created.stdout)["run_id"]
            context = run_cli(
                "context-record",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--doctor-call-id",
                "doctor",
                "--purge-call-id",
                "purge",
                "--doctor-summary",
                "all checks passed",
                "--started-at",
                "2026-08-19T01:29:00+00:00",
                "--completed-at",
                "2026-08-19T01:29:02+00:00",
            )
            self.assertEqual(context.returncode, 0, context.stderr)
            for index in range(1, 41):
                executed = run_cli(
                    "execute-query",
                    "--root",
                    str(root),
                    "--run-id",
                    run_id,
                    "--query-id",
                    f"q{index:02d}",
                    "--fixture-response",
                    str(fixture),
                    test_mode=True,
                )
                self.assertEqual(executed.returncode, 0, executed.stderr)

            indexed = run_cli(
                "context-index-record",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--host-call-id",
                "index",
                "--indexed-at",
                "2026-08-19T01:31:00+00:00",
            )
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            run_path = root / "runs" / run_id
            body = "The project launched publicly."
            (run_path / "pages" / "source.txt").write_text(body, encoding="utf-8")
            fetched = run_cli(
                "record-browser-fetch",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--url",
                "https://8.8.8.8/source",
                "--page",
                "pages/source.txt",
            )
            self.assertEqual(fetched.returncode, 0, fetched.stderr)
            reviewed = run_cli(
                "review-candidate",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--candidate-id",
                "candidate_q01_a1_001",
                "--rating",
                "A",
                "--claims-json",
                '[{"claim_id":"cl1","text":"The project launched publicly.","evidence_ids":[]}]',
                "--gap-type",
                "Contact",
            )
            self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
            evidence = run_cli(
                "record-evidence",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--candidate-id",
                "candidate_q01_a1_001",
                "--claim-id",
                "cl1",
                "--claim",
                "The project launched publicly.",
                "--source-url",
                "https://8.8.8.8/source",
                "--fetched-at",
                "2026-08-19T01:32:00+00:00",
                "--page",
                "pages/source.txt",
                "--excerpt",
                body,
                "--pattern",
                "launched publicly",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            for name, content in (
                ("candidate-cards.md", "# Candidate cards\n\nOne reviewed candidate.\n"),
                ("report.md", "# Report\n\nThe project launched publicly.\n"),
                ("run-report.md", "# Run report\n\n40 logical queries completed.\n"),
            ):
                (run_path / name).write_text(content, encoding="utf-8")
            finalized = run_cli(
                "finalize",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--status",
                "complete",
                "--stop-code",
                "SUCCESS",
                "--reason",
                "all gates passed",
                "--impact",
                "none",
                test_mode=True,
            )
            self.assertEqual(finalized.returncode, 0, finalized.stderr)
            guarded = run_cli("guard", "--root", str(root), "--run-id", run_id, test_mode=True)
            self.assertEqual(guarded.returncode, 0, guarded.stderr)


if __name__ == "__main__":
    unittest.main()
