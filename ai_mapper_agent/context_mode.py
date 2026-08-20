from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any

from .evidence import read_jsonl
from .run import Run


RESEARCH_EVENTS = frozenset({"query_attempt", "page_fetch", "evidence_recorded", "candidate_review"})


@dataclass(frozen=True)
class ContextPreflightReceipt:
    doctor_tool: str
    doctor_ok: bool
    doctor_summary: str
    purge_tool: str
    purge_ok: bool
    purge_scope: str
    project_dir: str
    context_dir: str
    started_at: str
    completed_at: str
    host_call_ids: tuple[str, str]


@dataclass(frozen=True)
class ContextFailureReceipt:
    doctor_tool: str
    doctor_ok: bool
    doctor_summary: str
    project_dir: str
    context_dir: str
    started_at: str
    completed_at: str
    host_call_id: str


@dataclass(frozen=True)
class ContextIndexReceipt:
    index_tool: str
    index_ok: bool
    paths: tuple[str, ...]
    indexed_at: str
    host_call_id: str


def require_context_environment(run: Run) -> None:
    """Require the lifecycle process to target this run's isolated Context Mode directories."""
    root = str(Path(run.manifest["agent_root"]).resolve())
    expected_context = str(Path(root) / ".context-mode")
    if (
        os.environ.get("CONTEXT_MODE_PROJECT_DIR") != root
        or os.environ.get("CONTEXT_MODE_DIR") != expected_context
    ):
        raise RuntimeError(
            "CONTEXT_MODE environment must target the Agent root and its isolated .context-mode directory"
        )


def _write_manifest_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def append_event(run: Run, event: dict[str, Any]) -> dict[str, Any]:
    if "sequence" in event:
        raise ValueError("event sequence is assigned by the run")
    prior = read_jsonl(run.path / "events.jsonl")
    row = {**event, "sequence": max((item.get("sequence", 0) for item in prior), default=0) + 1}
    with (run.path / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


def _validate_receipt(run: Run, receipt: ContextPreflightReceipt) -> None:
    if not isinstance(receipt, ContextPreflightReceipt):
        raise TypeError("receipt must be a ContextPreflightReceipt")
    if receipt.doctor_tool != "ctx_doctor" or receipt.purge_tool != "ctx_purge":
        raise ValueError("receipt must name the ctx_doctor and ctx_purge logical tools")
    if receipt.doctor_ok is not True or receipt.purge_ok is not True or not receipt.doctor_summary.strip():
        raise ValueError("Context Mode diagnostics and purge must both succeed")
    if receipt.purge_scope != "project":
        raise ValueError("Context Mode purge scope must be project")
    root = Path(run.manifest["agent_root"]).resolve()
    if Path(receipt.project_dir).resolve() != root:
        raise ValueError("receipt project directory does not match the agent root")
    expected_context = root / ".context-mode"
    if Path(receipt.context_dir).resolve() != expected_context:
        raise ValueError("receipt context directory is not the isolated agent directory")
    if len(receipt.host_call_ids) != 2 or any(not value.strip() for value in receipt.host_call_ids):
        raise ValueError("receipt requires two non-empty host call IDs")
    try:
        started = datetime.fromisoformat(receipt.started_at)
        completed = datetime.fromisoformat(receipt.completed_at)
    except ValueError as error:
        raise ValueError("receipt timestamps must be ISO 8601") from error
    if started.tzinfo is None or completed.tzinfo is None or completed < started:
        raise ValueError("receipt timestamps must be ordered and timezone-aware")


def record_context_preflight(run: Run, receipt: ContextPreflightReceipt) -> None:
    """Record one host-observed doctor-plus-project-purge receipt for this run."""
    _validate_receipt(run, receipt)
    events = read_jsonl(run.path / "events.jsonl")
    if any(event.get("event") == "context_preflight_failed" for event in events):
        raise RuntimeError("Context Mode preflight already failed for this run")
    append_event(run, {"event": "context_preflight", "receipt": asdict(receipt)})

    manifest_path = run.path / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["context_mode"] = {
        "status": "fresh_isolated",
        "project_dir": str(Path(receipt.project_dir).resolve()),
        "context_dir": str(Path(receipt.context_dir).resolve()),
        "purge_scope": receipt.purge_scope,
        "doctor_call_id": receipt.host_call_ids[0],
        "purge_call_id": receipt.host_call_ids[1],
        "completed_at": receipt.completed_at,
    }
    _write_manifest_atomic(manifest_path, manifest)


def require_context_preflight(run: Run) -> None:
    """Stop research unless this run has one successful isolated preflight."""
    manifest = json.loads((run.path / "run-manifest.json").read_text(encoding="utf-8"))
    context = manifest.get("context_mode", {})
    events = read_jsonl(run.path / "events.jsonl")
    preflights = [event for event in events if event.get("event") == "context_preflight"]
    if (
        context.get("status") != "fresh_isolated"
        or context.get("project_dir") != manifest.get("agent_root")
        or context.get("context_dir") != str(Path(manifest["agent_root"]) / ".context-mode")
        or context.get("purge_scope") != "project"
        or len(preflights) != 1
        or any(event.get("event") == "context_preflight_failed" for event in events)
    ):
        raise RuntimeError("Context Mode preflight must succeed before research")


def record_context_failure(run: Run, receipt: ContextFailureReceipt) -> None:
    """Record a failed doctor call so a no-research run can finish as blocked."""
    if not isinstance(receipt, ContextFailureReceipt):
        raise TypeError("receipt must be a ContextFailureReceipt")
    root = Path(run.manifest["agent_root"]).resolve()
    if (
        receipt.doctor_tool != "ctx_doctor"
        or receipt.doctor_ok is not False
        or not receipt.doctor_summary.strip()
        or Path(receipt.project_dir).resolve() != root
        or Path(receipt.context_dir).resolve() != root / ".context-mode"
        or not receipt.host_call_id.strip()
    ):
        raise ValueError("invalid Context Mode failure receipt")
    try:
        started = datetime.fromisoformat(receipt.started_at)
        completed = datetime.fromisoformat(receipt.completed_at)
    except ValueError as error:
        raise ValueError("receipt timestamps must be ISO 8601") from error
    if started.tzinfo is None or completed.tzinfo is None or completed < started:
        raise ValueError("receipt timestamps must be ordered and timezone-aware")
    append_event(run, {"event": "context_preflight_failed", "receipt": asdict(receipt)})
    manifest_path = run.path / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["context_mode"] = {
        "status": "failed",
        "project_dir": str(root),
        "context_dir": str(root / ".context-mode"),
        "doctor_call_id": receipt.host_call_id,
        "completed_at": receipt.completed_at,
        "failure_summary": receipt.doctor_summary,
    }
    _write_manifest_atomic(manifest_path, manifest)


def record_context_index(run: Run, receipt: ContextIndexReceipt) -> None:
    """Record the host ctx_index call that loads current-run Exa material."""
    require_context_preflight(run)
    if not isinstance(receipt, ContextIndexReceipt):
        raise TypeError("receipt must be a ContextIndexReceipt")
    required_paths = {"raw/exa-responses.jsonl", "candidates.jsonl"}
    if (
        receipt.index_tool != "ctx_index"
        or receipt.index_ok is not True
        or not required_paths.issubset(receipt.paths)
        or not receipt.host_call_id.strip()
    ):
        raise ValueError("invalid Context Mode index receipt")
    try:
        indexed_at = datetime.fromisoformat(receipt.indexed_at)
    except ValueError as error:
        raise ValueError("index timestamp must be ISO 8601") from error
    if indexed_at.tzinfo is None:
        raise ValueError("index timestamp must be timezone-aware")
    for relative in receipt.paths:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not (run.path / path).is_file():
            raise ValueError(f"invalid run-relative Context index path: {relative}")
    append_event(run, {"event": "context_results_indexed", "receipt": asdict(receipt)})
    manifest_path = run.path / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["context_mode"]["results_index_call_id"] = receipt.host_call_id
    manifest["context_mode"]["results_indexed_at"] = receipt.indexed_at
    _write_manifest_atomic(manifest_path, manifest)
