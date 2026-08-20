from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Any, Sequence

from .context_mode import (
    ContextFailureReceipt,
    ContextIndexReceipt,
    ContextPreflightReceipt,
    record_context_failure,
    record_context_index,
    record_context_preflight,
    require_context_environment,
)
from .exa import execute_query
from .evidence import record_candidate_review, record_evidence
from .fetch import fetch_public_page, record_browser_fetch
from .guard import final_guard
from .run import Run, create_run, finalize_run


def _emit(payload: dict[str, Any], *, stream=sys.stdout) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _load_run(root_value: str, run_id: str) -> Run:
    root = Path(root_value).resolve()
    if Path(run_id).name != run_id:
        raise ValueError("run_id must be a directory name")
    marker = root / ".ai-mapper-project"
    if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != str(root):
        raise ValueError("AI Mapper project marker is missing or mismatched")
    run_path = (root / "runs" / run_id).resolve()
    if not run_path.is_relative_to((root / "runs").resolve()):
        raise ValueError("run path escapes the project")
    manifest_path = run_path / "run-manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"run does not exist: {run_id}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("run_id") != run_id or Path(manifest.get("agent_root", "")).resolve() != root:
        raise ValueError("run manifest identity does not match the requested run")
    return Run(run_id=run_id, path=run_path, manifest=manifest)


class _FixtureTransport:
    def __init__(self, path: Path) -> None:
        self.path = path

    def post(self, url: str, payload: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        response = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(response, dict):
            raise ValueError("fixture response must be a JSON object")
        return response


def _mark_test_mode(run: Run) -> None:
    manifest_path = run.path / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["test_mode"] = True
    manifest["execution_mode"] = "offline_fixture"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _command_create(args: argparse.Namespace) -> int:
    now = datetime.fromisoformat(args.now) if args.now else datetime.now().astimezone()
    if now.tzinfo is None:
        raise ValueError("--now must include a timezone offset")
    run = create_run(Path(args.root), topic=args.topic, timezone_name=args.timezone, now=now)
    _emit({"ok": True, "run_id": run.run_id, "run_path": str(run.path)})
    return 0


def _command_context_record(args: argparse.Namespace) -> int:
    run = _load_run(args.root, args.run_id)
    project_dir = str(Path(run.manifest["agent_root"]).resolve())
    if args.failed:
        failure = ContextFailureReceipt(
            doctor_tool="ctx_doctor",
            doctor_ok=False,
            doctor_summary=args.doctor_summary,
            project_dir=project_dir,
            context_dir=str(Path(project_dir) / ".context-mode"),
            started_at=args.started_at,
            completed_at=args.completed_at,
            host_call_id=args.doctor_call_id,
        )
        record_context_failure(run, failure)
        _emit({"ok": True, "run_id": run.run_id, "context_mode": "failed"})
        return 0
    if not args.purge_call_id:
        raise ValueError("--purge-call-id is required for a successful preflight")
    require_context_environment(run)
    receipt = ContextPreflightReceipt(
        doctor_tool="ctx_doctor",
        doctor_ok=True,
        doctor_summary=args.doctor_summary,
        purge_tool="ctx_purge",
        purge_ok=True,
        purge_scope="project",
        project_dir=project_dir,
        context_dir=str(Path(project_dir) / ".context-mode"),
        started_at=args.started_at,
        completed_at=args.completed_at,
        host_call_ids=(args.doctor_call_id, args.purge_call_id),
    )
    record_context_preflight(run, receipt)
    _emit({"ok": True, "run_id": run.run_id, "context_mode": "fresh_isolated"})
    return 0


def _command_execute_query(args: argparse.Namespace) -> int:
    run = _load_run(args.root, args.run_id)
    fixture_response = getattr(args, "fixture_response", None)
    if fixture_response:
        _mark_test_mode(run)
        transport = _FixtureTransport(Path(fixture_response))
    else:
        transport = None
    response = execute_query(run, args.query_id, transport=transport)
    _emit({"ok": True, "run_id": run.run_id, "query_id": args.query_id, "result_count": len(response.get("results", []))})
    return 0


def _command_context_index_record(args: argparse.Namespace) -> int:
    run = _load_run(args.root, args.run_id)
    require_context_environment(run)
    record_context_index(
        run,
        ContextIndexReceipt(
            index_tool="ctx_index",
            index_ok=True,
            paths=("raw/exa-responses.jsonl", "candidates.jsonl"),
            indexed_at=args.indexed_at,
            host_call_id=args.host_call_id,
        ),
    )
    _emit({"ok": True, "run_id": run.run_id, "context_results": "indexed"})
    return 0


def _command_fetch(args: argparse.Namespace) -> int:
    run = _load_run(args.root, args.run_id)
    receipt = fetch_public_page(run, args.url, timeout=args.timeout)
    _emit({"ok": True, "run_id": run.run_id, "fetch": asdict(receipt)})
    return 0


def _command_record_browser_fetch(args: argparse.Namespace) -> int:
    run = _load_run(args.root, args.run_id)
    receipt = record_browser_fetch(run, args.url, args.page)
    _emit({"ok": True, "run_id": run.run_id, "fetch": asdict(receipt)})
    return 0


def _command_review_candidate(args: argparse.Namespace) -> int:
    run = _load_run(args.root, args.run_id)
    try:
        claims = json.loads(args.claims_json)
    except json.JSONDecodeError as error:
        raise ValueError("--claims-json must be valid JSON") from error
    candidate = record_candidate_review(
        run,
        candidate_id=args.candidate_id,
        rating=args.rating,
        claims=claims,
        gap_type=args.gap_type,
    )
    _emit({"ok": True, "run_id": run.run_id, "candidate_id": candidate["candidate_id"], "review_status": "reviewed"})
    return 0


def _command_record_evidence(args: argparse.Namespace) -> int:
    run = _load_run(args.root, args.run_id)
    from .context_mode import require_context_preflight

    require_context_preflight(run)
    relative = Path(args.page)
    pages_root = (run.path / "pages").resolve()
    page_path = (run.path / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not page_path.is_relative_to(pages_root) or not page_path.is_file():
        raise ValueError("--page must name an existing run-relative file under pages/")
    evidence = record_evidence(
        run,
        candidate_id=args.candidate_id,
        claim_id=args.claim_id,
        claim=args.claim,
        source_url=args.source_url,
        fetched_at=args.fetched_at,
        excerpt=args.excerpt,
        page_content=page_path.read_bytes().decode("utf-8", errors="replace"),
        verification_pattern=args.pattern,
    )
    _emit({"ok": True, "run_id": run.run_id, "evidence_id": evidence["evidence_id"]})
    return 0


def _command_guard(args: argparse.Namespace) -> int:
    run = _load_run(args.root, args.run_id)
    result = final_guard(run.path, allow_test_mode=os.environ.get("AI_MAPPER_TEST_MODE") == "1")
    _emit({"ok": result.ok, "run_id": run.run_id, "codes": list(result.codes)})
    return 0 if result.ok else 3


def _command_finalize(args: argparse.Namespace) -> int:
    run = _load_run(args.root, args.run_id)
    finalized = finalize_run(
        run,
        status=args.status,
        stop_code=args.stop_code,
        reason=args.reason,
        impact=args.impact,
        allow_test_mode=os.environ.get("AI_MAPPER_TEST_MODE") == "1",
    )
    _emit({"ok": True, "run_id": finalized.run_id, "status": finalized.manifest["status"]})
    return 0


def _add_run_selector(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", required=True)
    parser.add_argument("--run-id", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-mapper-agent", description="Run the auditable AI Mapper workflow")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="create one fixed-plan run")
    create.add_argument("--root", required=True)
    create.add_argument("--topic")
    create.add_argument("--timezone", default="Asia/Shanghai")
    create.add_argument("--now", help="timezone-aware ISO timestamp; intended for reproducible runs")
    create.set_defaults(handler=_command_create)

    context = commands.add_parser("context-record", help="record host-observed Context Mode doctor and purge receipts")
    _add_run_selector(context)
    context.add_argument("--doctor-call-id", required=True)
    context.add_argument("--purge-call-id")
    context.add_argument("--failed", action="store_true", help="record a failed ctx_doctor call without a purge")
    context.add_argument("--doctor-summary", required=True)
    context.add_argument("--started-at", required=True)
    context.add_argument("--completed-at", required=True)
    context.set_defaults(handler=_command_context_record)

    execute = commands.add_parser("execute-query", help="execute one query by saved query ID")
    _add_run_selector(execute)
    execute.add_argument("--query-id", required=True)
    if os.environ.get("AI_MAPPER_TEST_MODE") == "1":
        execute.add_argument("--fixture-response", help=argparse.SUPPRESS)
    execute.set_defaults(handler=_command_execute_query)

    context_index = commands.add_parser("context-index-record", help="record the host ctx_index call for current-run Exa results")
    _add_run_selector(context_index)
    context_index.add_argument("--host-call-id", required=True)
    context_index.add_argument("--indexed-at", required=True)
    context_index.set_defaults(handler=_command_context_index_record)

    fetch = commands.add_parser("fetch", help="fetch one safe public page over HTTP")
    _add_run_selector(fetch)
    fetch.add_argument("--url", required=True)
    fetch.add_argument("--timeout", type=float, default=15)
    fetch.set_defaults(handler=_command_fetch)

    browser = commands.add_parser("record-browser-fetch", help="record a run-local page fetched by the host browser")
    _add_run_selector(browser)
    browser.add_argument("--url", required=True)
    browser.add_argument("--page", required=True, help="run-relative path under pages/")
    browser.set_defaults(handler=_command_record_browser_fetch)

    review = commands.add_parser("review-candidate", help="review one unique candidate")
    _add_run_selector(review)
    review.add_argument("--candidate-id", required=True)
    review.add_argument("--rating", required=True, choices=("A", "B", "C", "暂不跟进"))
    review.add_argument("--claims-json", required=True)
    review.add_argument("--gap-type")
    review.set_defaults(handler=_command_review_candidate)

    evidence = commands.add_parser("record-evidence", help="record regex-verified evidence from a run-local page")
    _add_run_selector(evidence)
    evidence.add_argument("--candidate-id", required=True)
    evidence.add_argument("--claim-id", required=True)
    evidence.add_argument("--claim", required=True)
    evidence.add_argument("--source-url", required=True)
    evidence.add_argument("--fetched-at", required=True)
    evidence.add_argument("--page", required=True)
    evidence.add_argument("--excerpt", required=True)
    evidence.add_argument("--pattern", required=True)
    evidence.set_defaults(handler=_command_record_evidence)

    guard = commands.add_parser("guard", help="verify the finalized run")
    _add_run_selector(guard)
    guard.set_defaults(handler=_command_guard)

    finalize = commands.add_parser("finalize", help="finalize a complete, partial, or blocked run")
    _add_run_selector(finalize)
    finalize.add_argument("--status", required=True, choices=("complete", "partial", "blocked"))
    finalize.add_argument("--stop-code", required=True)
    finalize.add_argument("--reason", required=True)
    finalize.add_argument("--impact", required=True)
    finalize.set_defaults(handler=_command_finalize)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except Exception as error:
        _emit({"ok": False, "error": type(error).__name__, "message": str(error)}, stream=sys.stderr)
        return 2
