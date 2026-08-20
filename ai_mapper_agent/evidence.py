from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .run import Run
from .verification import verify_regex_claim


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _replace_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    temporary.replace(path)


def canonicalize_url(value: str) -> str:
    parsed = urlsplit(value)
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


def stable_claim_id(candidate_id: str, claim: str) -> str:
    normalized = " ".join(claim.split())
    return "claim_" + sha256(f"{candidate_id}\x00{normalized}".encode("utf-8")).hexdigest()[:16]


def _existing_canonical_candidates(run: Run) -> dict[str, str]:
    rows = read_jsonl(run.path / "candidates.jsonl")
    return {
        row["canonical_url"]: row["candidate_id"]
        for row in rows
        if row.get("duplicate_of") is None and isinstance(row.get("canonical_url"), str)
    }


def _assert_query_id(run: Run, query_id: str) -> None:
    planned_ids = {row["query_id"] for row in read_jsonl(run.path / "query-plan.jsonl")}
    if query_id not in planned_ids:
        raise ValueError(f"unknown query id: {query_id}")


def request_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def record_query_attempt(
    run: Run,
    *,
    query_id: str,
    attempt: int,
    request: dict[str, Any],
    status: str,
    response: dict[str, Any] | None = None,
    error_code: str | None = None,
) -> None:
    _assert_query_id(run, query_id)
    if attempt < 1:
        raise ValueError("attempt must be positive")
    _append_jsonl(
        run.path / "query-attempts.jsonl",
        {
            "query_id": query_id,
            "attempt": attempt,
            "request": request,
            "request_hash": request_hash(request),
            "status": status,
            "response": response,
            "error_code": error_code,
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    )
    from .context_mode import append_event

    append_event(run, {"event": "query_attempt", "query_id": query_id, "attempt": attempt, "status": status})


def record_final_execution(
    run: Run,
    *,
    query_id: str,
    final_attempt: int,
    status: str,
    result_count: int = 0,
    error_code: str | None = None,
) -> None:
    _assert_query_id(run, query_id)
    existing = [row for row in read_jsonl(run.path / "query-execution.jsonl") if row.get("query_id") == query_id]
    if existing:
        raise ValueError(f"final execution already recorded: {query_id}")
    _append_jsonl(
        run.path / "query-execution.jsonl",
        {
            "query_id": query_id,
            "final_attempt": final_attempt,
            "status": status,
            "result_count": result_count,
            "error_code": error_code,
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    )


def record_exa_response(
    run: Run,
    query_id: str,
    response: dict[str, Any],
    *,
    attempt: int = 1,
    request: dict[str, Any] | None = None,
    finalize: bool = True,
) -> None:
    """Persist a complete API response and one candidate row for every returned result."""
    _assert_query_id(run, query_id)
    results = response.get("results", [])
    if not isinstance(results, list):
        raise ValueError("Exa response results must be a list")
    received_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _append_jsonl(
        run.path / "raw" / "exa-responses.jsonl",
        {
            "query_id": query_id,
            "attempt": attempt,
            "request": request,
            "request_hash": request_hash(request) if request is not None else None,
            "received_at": received_at,
            "response": response,
        },
    )
    existing = _existing_canonical_candidates(run)
    for index, result in enumerate(results, start=1):
        if not isinstance(result, dict):
            raise ValueError("Exa result must be an object")
        url = result.get("url")
        if not isinstance(url, str) or not url:
            raise ValueError("Exa result has no URL")
        canonical_url = canonicalize_url(url)
        candidate_id = f"candidate_{query_id}_a{attempt}_{index:03d}"
        duplicate_of = existing.get(canonical_url)
        if duplicate_of is None:
            existing[canonical_url] = candidate_id
        _append_jsonl(
            run.path / "candidates.jsonl",
            {
                "candidate_id": candidate_id,
                "query_id": query_id,
                "returned_rank": index,
                "canonical_url": canonical_url,
                "url": url,
                "title": result.get("title"),
                "published_date": result.get("publishedDate"),
                "author": result.get("author"),
                "routing_highlights": result.get("highlights", []),
                "duplicate_of": duplicate_of,
                "review_status": "pending",
            },
        )
    if finalize:
        record_final_execution(
            run,
            query_id=query_id,
            final_attempt=attempt,
            status="completed" if results else "zero_results",
            result_count=len(results),
        )


def record_evidence(
    run: Run,
    *,
    candidate_id: str,
    claim_id: str,
    claim: str,
    source_url: str,
    fetched_at: str,
    excerpt: str,
    page_content: str,
    verification_pattern: str,
) -> dict[str, Any]:
    if not verification_pattern or len(verification_pattern) > 500:
        raise ValueError("verification pattern must contain 1-500 characters")
    verification = verify_regex_claim(page_content, verification_pattern)
    if not verification.matched or excerpt not in page_content or re.search(verification_pattern, excerpt, flags=re.IGNORECASE) is None:
        raise ValueError("claim evidence did not verify against the fetched page")
    content_hash = sha256(page_content.encode("utf-8")).hexdigest()
    if not claim_id.strip():
        raise ValueError("claim_id is required")
    candidate_rows = read_jsonl(run.path / "candidates.jsonl")
    matching_candidates = [row for row in candidate_rows if row.get("candidate_id") == candidate_id]
    if len(matching_candidates) == 1:
        candidate_claims = matching_candidates[0].get("claims", [])
        matching_claims = [item for item in candidate_claims if isinstance(item, dict) and item.get("claim_id") == claim_id]
        if matching_claims and matching_claims[0].get("text") != claim:
            raise ValueError("evidence claim text must match the candidate claim")
    evidence_id = "e_" + sha256(
        f"{candidate_id}\x00{claim_id}\x00{claim}\x00{source_url}\x00{content_hash}".encode("utf-8")
    ).hexdigest()[:16]
    row = {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "claim_id": claim_id,
        "claim": claim,
        "source_url": canonicalize_url(source_url),
        "fetched_at": fetched_at,
        "excerpt": excerpt,
        "content_hash": content_hash,
        "verification_pattern": verification_pattern,
        "verification_status": "regex_matched",
        "match_start": verification.match_start,
        "match_end": verification.match_end,
    }
    _append_jsonl(run.path / "evidence.jsonl", row)
    if len(matching_candidates) == 1:
        for candidate in candidate_rows:
            if candidate.get("candidate_id") != candidate_id:
                continue
            for candidate_claim in candidate.get("claims", []):
                if isinstance(candidate_claim, dict) and candidate_claim.get("claim_id") == claim_id:
                    evidence_ids = candidate_claim.setdefault("evidence_ids", [])
                    if row["evidence_id"] not in evidence_ids:
                        evidence_ids.append(row["evidence_id"])
        _replace_jsonl(run.path / "candidates.jsonl", candidate_rows)
    from .context_mode import append_event

    append_event(run, {"event": "evidence_recorded", "candidate_id": candidate_id, "claim_id": claim_id})
    return row


def record_candidate_review(
    run: Run,
    *,
    candidate_id: str,
    rating: str,
    claims: list[dict[str, Any]],
    gap_type: str | None = None,
) -> dict[str, Any]:
    """Atomically rewrite one unique candidate with its reviewed rating and claims."""
    from .context_mode import append_event, require_context_preflight

    require_context_preflight(run)
    if rating not in {"A", "B", "C", "暂不跟进"}:
        raise ValueError("rating must be A, B, C, or 暂不跟进")
    if not isinstance(claims, list) or any(not isinstance(claim, dict) for claim in claims):
        raise ValueError("claims must be a list of objects")
    rows = read_jsonl(run.path / "candidates.jsonl")
    matches = [row for row in rows if row.get("candidate_id") == candidate_id]
    if len(matches) != 1:
        raise ValueError(f"candidate must exist exactly once: {candidate_id}")
    candidate = matches[0]
    if candidate.get("duplicate_of") is not None:
        raise ValueError("duplicate candidates are reviewed through their unique canonical candidate")
    candidate.update({"review_status": "reviewed", "rating": rating, "claims": claims})
    if gap_type is not None:
        candidate["gap_type"] = gap_type
    _replace_jsonl(run.path / "candidates.jsonl", rows)
    append_event(run, {"event": "candidate_review", "candidate_id": candidate_id, "rating": rating})
    return candidate


def record_fetch(
    run: Run,
    *,
    url: str,
    status: str,
    path: str | None = None,
    reason: str | None = None,
    method: str = "http",
    byte_count: int | None = None,
    content_hash: str | None = None,
) -> None:
    row = {
        "url": canonicalize_url(url),
        "method": method,
        "status": status,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "path": path,
        "byte_count": byte_count,
        "content_hash": content_hash,
        "reason": reason,
    }
    _append_jsonl(run.path / "fetches.jsonl", row)
    from .context_mode import append_event

    append_event(run, {"event": "page_fetch", "url": row["url"], "status": status, "method": method})
