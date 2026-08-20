from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

from .contract import MAX_FETCHED_PAGES, RUN_STATUSES, TERMINAL_QUERY_STATUSES
from .context_mode import RESEARCH_EVENTS
from .evidence import canonicalize_url, read_jsonl, request_hash
from .exa import build_search_payload
from .plan import validate_query_plan
from .plan import build_query_plan, plan_hash
from datetime import date


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    codes: tuple[str, ...]


def _manifest(run_path: Path) -> dict:
    return json.loads((run_path / "run-manifest.json").read_text(encoding="utf-8"))


def _check_context_mode(run_path: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    context = manifest.get("context_mode", {})
    root = manifest.get("agent_root")
    events = read_jsonl(run_path / manifest["artifacts"]["events.jsonl"])
    research = [event for event in events if event.get("event") in RESEARCH_EVENTS]
    failures = [event for event in events if event.get("event") == "context_preflight_failed"]
    if manifest.get("status") == "blocked" and manifest.get("stop_code") == "CONTEXT_MODE_UNAVAILABLE":
        successes = [event for event in events if event.get("event") == "context_preflight"]
        if len(failures) != 1 or successes or research:
            errors.append("CONTEXT_MODE_FAILURE_PATH_INVALID")
            return errors
        if [event.get("sequence") for event in events] != list(range(1, len(events) + 1)):
            errors.append("EVENT_SEQUENCE_INVALID")
        marker = Path(root) / ".ai-mapper-project"
        if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != root:
            errors.append("CONTEXT_MODE_PROJECT_MARKER")
        receipt = failures[0].get("receipt", {})
        if (
            context.get("status") != "failed"
            or context.get("project_dir") != root
            or context.get("context_dir") != str(Path(root) / ".context-mode")
            or receipt.get("doctor_tool") != "ctx_doctor"
            or receipt.get("doctor_ok") is not False
            or not receipt.get("doctor_summary")
            or receipt.get("project_dir") != root
            or receipt.get("context_dir") != str(Path(root) / ".context-mode")
            or context.get("doctor_call_id") != receipt.get("host_call_id")
        ):
            errors.append("CONTEXT_MODE_FAILURE_RECEIPT_INVALID")
        return errors
    if failures:
        errors.append("CONTEXT_MODE_FAILURE_PATH_INVALID")
    if context.get("status") != "fresh_isolated":
        errors.append("CONTEXT_MODE_NOT_FRESH")
    if context.get("project_dir") != root or context.get("context_dir") != str(Path(root) / ".context-mode"):
        errors.append("CONTEXT_MODE_NOT_ISOLATED")
    if context.get("purge_scope") != "project":
        errors.append("CONTEXT_MODE_PURGE_SCOPE")
    marker = Path(root) / ".ai-mapper-project"
    if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != root:
        errors.append("CONTEXT_MODE_PROJECT_MARKER")
    if [event.get("sequence") for event in events] != list(range(1, len(events) + 1)):
        errors.append("EVENT_SEQUENCE_INVALID")
    preflights = [event for event in events if event.get("event") == "context_preflight"]
    if len(preflights) != 1:
        errors.append("CONTEXT_MODE_PURGE_COUNT")
        return errors
    preflight = preflights[0]
    receipt = preflight.get("receipt", {})
    host_ids = receipt.get("host_call_ids")
    if (
        receipt.get("doctor_tool") != "ctx_doctor"
        or receipt.get("doctor_ok") is not True
        or not receipt.get("doctor_summary")
        or receipt.get("purge_tool") != "ctx_purge"
        or receipt.get("purge_ok") is not True
        or receipt.get("purge_scope") != "project"
        or receipt.get("project_dir") != root
        or receipt.get("context_dir") != str(Path(root) / ".context-mode")
        or not isinstance(host_ids, list)
        or len(host_ids) != 2
        or any(not isinstance(value, str) or not value for value in host_ids)
    ):
        errors.append("CONTEXT_MODE_RECEIPT_INVALID")
    if context.get("doctor_call_id") != (host_ids[0] if isinstance(host_ids, list) and len(host_ids) == 2 else None):
        errors.append("CONTEXT_MODE_RECEIPT_INVALID")
    if context.get("purge_call_id") != (host_ids[1] if isinstance(host_ids, list) and len(host_ids) == 2 else None):
        errors.append("CONTEXT_MODE_RECEIPT_INVALID")
    if research and preflight.get("sequence", 0) >= min(event.get("sequence", 0) for event in research):
        errors.append("CONTEXT_MODE_ORDER")
    if read_jsonl(run_path / "raw" / "exa-responses.jsonl"):
        indexes = [event for event in events if event.get("event") == "context_results_indexed"]
        if len(indexes) != 1:
            errors.append("CONTEXT_RESULTS_NOT_INDEXED")
        else:
            index_event = indexes[0]
            receipt = index_event.get("receipt", {})
            required_paths = {"raw/exa-responses.jsonl", "candidates.jsonl"}
            query_sequences = [event.get("sequence", 0) for event in events if event.get("event") == "query_attempt"]
            if (
                receipt.get("index_tool") != "ctx_index"
                or receipt.get("index_ok") is not True
                or not isinstance(receipt.get("paths"), list)
                or not required_paths.issubset(receipt.get("paths", []))
                or context.get("results_index_call_id") != receipt.get("host_call_id")
                or (query_sequences and index_event.get("sequence", 0) <= max(query_sequences))
            ):
                errors.append("CONTEXT_RESULTS_INDEX_INVALID")
    return errors


def _check_queries(run_path: Path, plan_rows: list[dict], *, require_complete: bool) -> list[str]:
    execution_rows = read_jsonl(run_path / "query-execution.jsonl")
    attempt_rows = read_jsonl(run_path / "query-attempts.jsonl")
    planned_rows = {row.get("query_id"): row for row in plan_rows}
    planned = set(planned_rows)
    errors: list[str] = []
    by_query = {query_id: [row for row in execution_rows if row.get("query_id") == query_id] for query_id in planned}
    if (
        any(len(rows) > 1 for rows in by_query.values())
        or any(row.get("query_id") not in planned for row in execution_rows)
        or (require_complete and any(len(rows) != 1 for rows in by_query.values()))
    ):
        errors.append("QUERY_FINAL_STATUS_COUNT")
    if any(rows and rows[0].get("status") not in TERMINAL_QUERY_STATUSES for rows in by_query.values()) or (
        require_complete and any(len(rows) != 1 for rows in by_query.values())
    ):
        errors.append("QUERY_NOT_TERMINAL")
    if require_complete and any(rows and rows[0].get("status") not in {"completed", "zero_results"} for rows in by_query.values()):
        errors.append("QUERY_NOT_SUCCESSFUL")

    attempts_by_query = {query_id: [row for row in attempt_rows if row.get("query_id") == query_id] for query_id in planned}
    if any(row.get("query_id") not in planned for row in attempt_rows):
        errors.append("EXA_REQUEST_PLAN_MISMATCH")
    for query_id, plan_row in planned_rows.items():
        attempts = attempts_by_query[query_id]
        expected_request = build_search_payload(plan_row)
        expected_hash = request_hash(expected_request)
        if len(attempts) > 3 or (require_complete and not attempts):
            errors.append("QUERY_ATTEMPT_COUNT")
            continue
        if not attempts:
            continue
        if [row.get("attempt") for row in attempts] != list(range(1, len(attempts) + 1)):
            errors.append("QUERY_ATTEMPT_SEQUENCE")
        if any(row.get("request") != expected_request or row.get("request_hash") != expected_hash for row in attempts):
            errors.append("EXA_REQUEST_PLAN_MISMATCH")
        final_rows = by_query[query_id]
        if not final_rows:
            errors.append("QUERY_FINAL_STATUS_COUNT")
        if len(final_rows) == 1 and final_rows[0].get("final_attempt") != attempts[-1].get("attempt"):
            errors.append("QUERY_FINAL_ATTEMPT_MISMATCH")

    raw_rows = read_jsonl(run_path / "raw" / "exa-responses.jsonl")
    raw_ids = {row.get("query_id") for row in raw_rows}
    completed_ids = {query_id for query_id, rows in by_query.items() if len(rows) == 1 and rows[0].get("status") in {"completed", "zero_results"}}
    if not completed_ids.issubset(raw_ids):
        errors.append("RAW_EXA_RESPONSE_MISSING")
    for raw in raw_rows:
        plan_row = planned_rows.get(raw.get("query_id"))
        if plan_row is None:
            errors.append("EXA_REQUEST_PLAN_MISMATCH")
            continue
        expected_request = build_search_payload(plan_row)
        if raw.get("request") != expected_request or raw.get("request_hash") != request_hash(expected_request):
            errors.append("EXA_REQUEST_PLAN_MISMATCH")
    candidates = read_jsonl(run_path / "candidates.jsonl")
    if any(row.get("query_id") not in planned for row in candidates):
        errors.append("CANDIDATE_RESULT_MISMATCH")
    for query_id in planned:
        finals = by_query[query_id]
        if len(finals) != 1 or finals[0].get("status") not in {"completed", "zero_results"}:
            continue
        matching_raw = [row for row in raw_rows if row.get("query_id") == query_id]
        if len(matching_raw) != 1:
            errors.append("RAW_EXA_RESPONSE_COUNT")
            continue
        raw = matching_raw[0]
        response = raw.get("response", {})
        results = response.get("results") if isinstance(response, dict) else None
        if not isinstance(results, list):
            errors.append("RAW_EXA_RESPONSE_INVALID")
            continue
        final = finals[0]
        expected_status = "completed" if results else "zero_results"
        if (
            final.get("result_count") != len(results)
            or final.get("status") != expected_status
            or raw.get("attempt") != final.get("final_attempt")
        ):
            errors.append("RAW_RESULT_COUNT_MISMATCH")
        successful_attempts = [row for row in attempts_by_query[query_id] if row.get("status") == "success"]
        if len(successful_attempts) != 1 or successful_attempts[0].get("response") != response:
            errors.append("RAW_ATTEMPT_MISMATCH")
        query_candidates = [row for row in candidates if row.get("query_id") == query_id]
        if len(query_candidates) != len(results):
            errors.append("CANDIDATE_RESULT_MISMATCH")
            continue
        by_rank = {row.get("returned_rank"): row for row in query_candidates}
        for rank, result in enumerate(results, start=1):
            candidate = by_rank.get(rank)
            url = result.get("url") if isinstance(result, dict) else None
            if (
                candidate is None
                or not isinstance(url, str)
                or candidate.get("url") != url
                or candidate.get("canonical_url") != canonicalize_url(url)
            ):
                errors.append("CANDIDATE_RESULT_MISMATCH")
    return errors


def _check_run_structure(
    run_path: Path,
    manifest: dict,
    *,
    expected_status: str | None,
    check_pointers: bool,
    allow_test_mode: bool,
) -> list[str]:
    errors: list[str] = []
    status = manifest.get("status")
    if manifest.get("test_mode") is True and not allow_test_mode:
        errors.append("TEST_MODE_RUN")
    if status not in RUN_STATUSES:
        errors.append("RUN_STATUS_INVALID")
    if status == "in_progress":
        errors.append("RUN_NOT_FINALIZED")
    if expected_status is not None and status != expected_status:
        errors.append("RUN_STATUS_MISMATCH")
    if manifest.get("run_id") != run_path.name or Path(manifest.get("agent_root", "")).resolve() != run_path.parent.parent.resolve():
        errors.append("RUN_IDENTITY_MISMATCH")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("ARTIFACT_MAP_INVALID")
    else:
        for value in artifacts.values():
            if not isinstance(value, str) or Path(value).is_absolute() or ".." in Path(value).parts:
                errors.append("ARTIFACT_PATH_INVALID")
                continue
            if not (run_path / value).is_file():
                errors.append("ARTIFACT_MISSING")
    if any(not (run_path / name).is_file() or not (run_path / name).read_text(encoding="utf-8").strip() for name in ("candidate-cards.md", "report.md", "run-report.md")):
        errors.append("REPORT_EMPTY")
    if status in RUN_STATUSES - {"in_progress"} and any(
        not isinstance(manifest.get(field), str) or not manifest.get(field).strip()
        for field in ("stop_code", "stop_reason", "impact", "finalized_at")
    ):
        errors.append("STOP_DETAILS_MISSING")
    if check_pointers and status in RUN_STATUSES - {"in_progress"}:
        latest_name = "latest-test.json" if manifest.get("test_mode") is True else "latest.json"
        latest_path = run_path.parent / latest_name
        if not latest_path.is_file():
            errors.append("LATEST_POINTER_INVALID")
        else:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            if latest.get("run_id") != run_path.name or latest.get("status") != status:
                errors.append("LATEST_POINTER_INVALID")
        if status == "complete" and manifest.get("test_mode") is not True:
            complete_path = run_path.parent / "latest-complete.json"
            if not complete_path.is_file():
                errors.append("LATEST_COMPLETE_POINTER_INVALID")
            else:
                latest_complete = json.loads(complete_path.read_text(encoding="utf-8"))
                if latest_complete.get("run_id") != run_path.name or latest_complete.get("status") != "complete":
                    errors.append("LATEST_COMPLETE_POINTER_INVALID")
    return errors


def _check_candidates_and_evidence(run_path: Path) -> list[str]:
    candidates = read_jsonl(run_path / "candidates.jsonl")
    evidence = read_jsonl(run_path / "evidence.jsonl")
    errors: list[str] = []
    candidate_ids = [row.get("candidate_id") for row in candidates]
    if len(candidate_ids) != len(set(candidate_ids)) or any(not isinstance(value, str) or not value for value in candidate_ids):
        errors.append("CANDIDATE_ID_INVALID")
    evidence_ids = [row.get("evidence_id") for row in evidence]
    if len(evidence_ids) != len(set(evidence_ids)) or any(not isinstance(value, str) or not value for value in evidence_ids):
        errors.append("EVIDENCE_ID_INVALID")
    known_candidates = set(candidate_ids)
    evidence_by_id = {row.get("evidence_id"): row for row in evidence}
    successful_fetches = {
        (row.get("url"), row.get("content_hash")): row
        for row in read_jsonl(run_path / "fetches.jsonl")
        if row.get("status") == "success"
    }
    for row in evidence:
        if row.get("candidate_id") not in known_candidates:
            errors.append("EVIDENCE_CANDIDATE_UNKNOWN")
        if (
            not row.get("claim_id")
            or not row.get("source_url")
            or not row.get("excerpt")
            or not row.get("content_hash")
        ):
            errors.append("EVIDENCE_RECORD_INVALID")
        fetch = successful_fetches.get((row.get("source_url"), row.get("content_hash")))
        if fetch is None:
            errors.append("EVIDENCE_FETCH_MISSING")
            continue
        page_path = fetch.get("path")
        if not isinstance(page_path, str) or not (run_path / page_path).is_file():
            errors.append("EVIDENCE_FETCH_MISSING")
            continue
        page_text = (run_path / page_path).read_bytes().decode("utf-8", errors="replace")
        pattern = row.get("verification_pattern")
        try:
            match = re.search(pattern, page_text, flags=re.IGNORECASE) if isinstance(pattern, str) and len(pattern) <= 500 else None
        except re.error:
            match = None
        if (
            row.get("verification_status") != "regex_matched"
            or not isinstance(row.get("excerpt"), str)
            or row["excerpt"] not in page_text
            or match is None
            or re.search(pattern, row["excerpt"], flags=re.IGNORECASE) is None
            or row.get("match_start") != match.start()
            or row.get("match_end") != match.end()
        ):
            errors.append("REGEX_EVIDENCE_MISMATCH")
    first_by_url: dict[str, str] = {}
    for row in candidates:
        canonical_url = row.get("canonical_url")
        if not isinstance(canonical_url, str):
            errors.append("CANDIDATE_RESULT_MISMATCH")
            continue
        expected_duplicate = first_by_url.get(canonical_url)
        if row.get("duplicate_of") != expected_duplicate:
            errors.append("DUPLICATE_LINK_INVALID")
        if expected_duplicate is None:
            first_by_url[canonical_url] = row.get("candidate_id")
    unique = [row for row in candidates if row.get("duplicate_of") is None]
    if any(row.get("review_status") != "reviewed" for row in unique):
        errors.append("CANDIDATE_REVIEW_INCOMPLETE")
    allowed_ratings = {"A", "B", "C", "暂不跟进"}
    if any(row.get("rating") not in allowed_ratings for row in unique):
        errors.append("RATING_INVALID")
    for row in unique:
        if row.get("rating") not in {"A", "B"}:
            continue
        claims = row.get("claims")
        if not isinstance(claims, list) or not claims:
            errors.append("A_B_EVIDENCE_MISSING")
            continue
        claim_ids = [claim.get("claim_id") for claim in claims if isinstance(claim, dict)]
        if len(claim_ids) != len(claims) or len(claim_ids) != len(set(claim_ids)) or any(not value for value in claim_ids):
            errors.append("CLAIM_ID_INVALID")
            continue
        for claim in claims:
            linked_ids = claim.get("evidence_ids", [])
            if not isinstance(linked_ids, list) or not linked_ids:
                errors.append("A_B_EVIDENCE_MISSING")
                continue
            linked = [evidence_by_id.get(evidence_id) for evidence_id in linked_ids]
            if any(item is None for item in linked):
                errors.append("A_B_EVIDENCE_MISSING")
            if not any(
                item is not None
                and item.get("candidate_id") == row.get("candidate_id")
                and item.get("claim_id") == claim.get("claim_id")
                and item.get("claim") == claim.get("text")
                and item.get("source_url")
                and item.get("excerpt")
                and item.get("content_hash")
                for item in linked
            ):
                errors.append("CLAIM_EVIDENCE_MISMATCH")
            if any(
                item is not None
                and item.get("candidate_id") == row.get("candidate_id")
                and item.get("claim_id") == claim.get("claim_id")
                and item.get("claim") != claim.get("text")
                for item in linked
            ):
                errors.append("CLAIM_TEXT_MISMATCH")
    return errors


def _check_fetches(run_path: Path) -> list[str]:
    errors: list[str] = []
    fetches = read_jsonl(run_path / "fetches.jsonl")
    occupied_urls = {row.get("url") for row in fetches if row.get("status") in {"reserved", "success"}}
    if len(occupied_urls) > MAX_FETCHED_PAGES:
        errors.append("FETCH_CAP_EXCEEDED")
    pages_root = (run_path / "pages").resolve()
    for row in (item for item in fetches if item.get("status") == "success"):
        path_value = row.get("path")
        if (
            row.get("method") not in {"http", "browser"}
            or not isinstance(path_value, str)
            or not isinstance(row.get("byte_count"), int)
            or not isinstance(row.get("content_hash"), str)
        ):
            errors.append("FETCH_RECEIPT_INVALID")
            continue
        relative = Path(path_value)
        if relative.is_absolute() or ".." in relative.parts:
            errors.append("FETCH_PATH_INVALID")
            continue
        page = (run_path / relative).resolve()
        if not page.is_relative_to(pages_root):
            errors.append("FETCH_PATH_INVALID")
            continue
        if not page.is_file():
            errors.append("FETCH_ARTIFACT_MISSING")
            continue
        body = page.read_bytes()
        if len(body) != row["byte_count"] or sha256(body).hexdigest() != row["content_hash"]:
            errors.append("FETCH_HASH_MISMATCH")
    return errors


def final_guard(
    run_path: Path,
    *,
    expected_status: str | None = None,
    check_pointers: bool = True,
    allow_test_mode: bool = False,
) -> GuardResult:
    """Check process completeness without inventing a candidate-count quota."""
    manifest = _manifest(run_path)
    errors = _check_run_structure(
        run_path,
        manifest,
        expected_status=expected_status,
        check_pointers=check_pointers,
        allow_test_mode=allow_test_mode,
    )
    plan_rows = read_jsonl(run_path / "query-plan.jsonl")
    errors.extend(validate_query_plan(plan_rows).errors)
    expected_plan = build_query_plan(
        topic=manifest.get("topic"),
        run_date=date.fromisoformat(manifest["run_date"]),
        timezone_name=manifest.get("timezone", "Asia/Shanghai"),
    )
    if plan_rows != expected_plan or manifest.get("query_plan_hash") != plan_hash(plan_rows):
        errors.append("QUERY_PLAN_TAMPERED")
    errors.extend(_check_context_mode(run_path, manifest))
    errors.extend(_check_queries(run_path, plan_rows, require_complete=manifest.get("status") not in {"partial", "blocked"}))
    errors.extend(_check_fetches(run_path))
    errors.extend(_check_candidates_and_evidence(run_path))
    return GuardResult(ok=not errors, codes=tuple(dict.fromkeys(errors)))
