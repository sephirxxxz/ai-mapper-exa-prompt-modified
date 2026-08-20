from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import AGENT_VERSION
from .contract import RUN_SCHEMA_VERSION, RUN_STATUSES
from .plan import build_query_plan, plan_hash


@dataclass(frozen=True)
class Run:
    run_id: str
    path: Path
    manifest: dict[str, Any]


_EMPTY_ARTIFACTS = (
    "events.jsonl",
    "query-attempts.jsonl",
    "query-execution.jsonl",
    "candidates.jsonl",
    "evidence.jsonl",
    "fetches.jsonl",
    "raw/exa-responses.jsonl",
)
_TEXT_ARTIFACTS = ("candidate-cards.md", "report.md", "run-report.md")


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _run_id(now: datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%S%z")


def _next_run_id(runs_path: Path, now: datetime) -> str:
    base_id = _run_id(now)
    if not (runs_path / base_id).exists():
        return base_id
    suffix = 2
    while (runs_path / f"{base_id}-{suffix:02d}").exists():
        suffix += 1
    return f"{base_id}-{suffix:02d}"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_run(path: Path) -> Run:
    manifest_path = path / "run-manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"run manifest is missing: {path.name}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return Run(run_id=path.name, path=path, manifest=manifest)


def _ensure_project_marker(root: Path) -> None:
    marker = root / ".ai-mapper-project"
    expected = str(root)
    if marker.exists() and marker.read_text(encoding="utf-8").strip() != expected:
        raise ValueError("project marker does not match the AI Mapper root")
    marker.write_text(expected + "\n", encoding="utf-8")


def create_run(root: Path, *, topic: str | None, timezone_name: str, now: datetime) -> Run:
    """Create a new local run and persist the complete fixed query plan."""
    try:
        local_now = now.astimezone(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"unknown timezone: {timezone_name}") from error

    root = root.resolve()
    _ensure_project_marker(root)
    runs_path = root / "runs"
    run_id = _next_run_id(runs_path, local_now)
    run_path = runs_path / run_id
    (run_path / "raw").mkdir(parents=True)
    (run_path / "pages").mkdir()

    for relative_path in _EMPTY_ARTIFACTS:
        (run_path / relative_path).touch()
    for relative_path in _TEXT_ARTIFACTS:
        (run_path / relative_path).write_text("", encoding="utf-8")

    query_plan = build_query_plan(topic=topic, run_date=local_now.date(), timezone_name=timezone_name)
    (run_path / "query-plan.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in query_plan),
        encoding="utf-8",
    )
    manifest: dict[str, Any] = {
        "schema_version": RUN_SCHEMA_VERSION,
        "agent_version": AGENT_VERSION,
        "run_id": run_id,
        "agent_root": str(root),
        "topic": topic,
        "timezone": timezone_name,
        "started_at_local": _iso(local_now),
        "started_at_utc": _iso(local_now.astimezone(timezone.utc)),
        "run_date": local_now.date().isoformat(),
        "status": "in_progress",
        "phase": "created",
        "query_count": len(query_plan),
        "query_plan_hash": plan_hash(query_plan),
        "completed_phases": [],
        "context_mode": {"status": "not_started"},
        "cost": {"observed_usd": None, "currency": "USD"},
        "stop_code": None,
        "stop_reason": None,
        "impact": None,
        "artifacts": {relative: relative for relative in (*_EMPTY_ARTIFACTS, *_TEXT_ARTIFACTS, "query-plan.jsonl")},
    }
    _write_json(run_path / "run-manifest.json", manifest)
    return Run(run_id=run_id, path=run_path, manifest=manifest)


def finalize_run(
    run: Run,
    *,
    status: str,
    stop_code: str,
    reason: str,
    impact: str,
    allow_test_mode: bool = False,
) -> Run:
    """Finalize a run only after its status-appropriate Guard checks pass."""
    if status not in RUN_STATUSES - {"in_progress"}:
        raise ValueError(f"invalid final status: {status}")
    if not all(isinstance(value, str) and value.strip() for value in (stop_code, reason, impact)):
        raise ValueError("stop_code, reason, and impact must be non-empty")
    for relative in _TEXT_ARTIFACTS:
        path = run.path / relative
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise ValueError(f"required report is empty: {relative}")

    manifest_path = run.path / "run-manifest.json"
    original = json.loads(manifest_path.read_text(encoding="utf-8"))
    if original.get("status") != "in_progress":
        raise ValueError(f"run is already finalized: {original.get('status')}")
    if original.get("test_mode") is True and not allow_test_mode:
        raise ValueError("test-mode runs cannot use production finalization")
    manifest = dict(original)
    finalized_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest.update(
        {
            "status": status,
            "phase": "finalized",
            "stop_code": stop_code,
            "stop_reason": reason,
            "impact": impact,
            "finalized_at": finalized_at,
        }
    )
    _write_json(manifest_path, manifest)

    from .guard import final_guard

    result = final_guard(run.path, expected_status=status, check_pointers=False, allow_test_mode=allow_test_mode)
    if not result.ok:
        _write_json(manifest_path, original)
        raise ValueError(f"final guard failed: {', '.join(result.codes)}")

    pointer = {"run_id": run.run_id, "status": status, "finalized_at": finalized_at}
    runs_path = run.path.parent
    if manifest.get("test_mode") is True:
        _write_json(runs_path / "latest-test.json", pointer)
    else:
        _write_json(runs_path / "latest.json", pointer)
    if status == "complete" and manifest.get("test_mode") is not True:
        _write_json(runs_path / "latest-complete.json", pointer)
    return _read_run(run.path)


def resume_run(root: Path, run_id: str, *, now: datetime) -> Run:
    """Resume only the same local calendar day; cross-day reuse is forbidden."""
    run = _read_run(root.resolve() / "runs" / run_id)
    timezone_name = run.manifest.get("timezone")
    if not isinstance(timezone_name, str):
        raise ValueError("run manifest has no timezone")
    local_date = now.astimezone(ZoneInfo(timezone_name)).date().isoformat()
    if local_date != run.manifest.get("run_date"):
        raise ValueError("cross-day resume is forbidden; create a new run")
    return run
