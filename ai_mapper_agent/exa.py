from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .run import Run


SEARCH_URL = "https://api.exa.ai/search"
MAX_ATTEMPTS = 3


class ExaError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class TransientExaError(ExaError):
    """A temporary Exa or network failure that may be retried."""


class AuthenticationExaError(ExaError):
    """An invalid or unauthorized Exa credential."""


class CreditsExhaustedError(ExaError):
    """An Exa account whose usable credits are exhausted."""


def _validate_search_response(response: object) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise ExaError("Exa response must be a JSON object", code="INVALID_RESPONSE")
    results = response.get("results")
    if not isinstance(results, list) or any(
        not isinstance(result, dict) or not isinstance(result.get("url"), str) or not result.get("url")
        for result in results
    ):
        raise ExaError("Exa response results must be a list of URL objects", code="INVALID_RESPONSE")
    return response


def build_search_payload(row: dict[str, Any]) -> dict[str, Any]:
    """Translate one approved query-plan row into the sole supported Exa request."""
    if row.get("type") != "auto" or row.get("num_results") != 10:
        raise ValueError("only approved auto query-plan rows may be executed")
    return {
        "query": row["query"],
        "type": "auto",
        "numResults": 10,
        "startPublishedDate": row["start_published_date"],
        "endPublishedDate": row["end_published_date"],
        "contents": {"highlights": True},
    }


def require_plan_row(plan_path: Path, query_id: str) -> dict[str, Any]:
    if not isinstance(query_id, str):
        raise TypeError("query_id must be a string from the saved query plan")
    rows = [json.loads(line) for line in plan_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    matches = [row for row in rows if row.get("query_id") == query_id]
    if len(matches) != 1:
        raise ValueError(f"unknown or duplicate query id: {query_id}")
    return matches[0]


class UrllibTransport:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("EXA_API_KEY")

    def post(self, url: str, payload: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        if not self.api_key:
            raise AuthenticationExaError("EXA_API_KEY is required", code="MISSING_API_KEY")
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed HTTPS API endpoint
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            code = f"HTTP_{error.code}"
            if error.code in {401, 403}:
                raise AuthenticationExaError("Exa authentication failed", code=code) from error
            if error.code == 402:
                raise CreditsExhaustedError("Exa credits are exhausted", code=code) from error
            if error.code in {408, 429} or error.code >= 500:
                raise TransientExaError("Exa temporarily unavailable", code=code) from error
            raise ExaError("Exa request failed", code=code) from error
        except (TimeoutError, URLError) as error:
            raise TransientExaError("Exa network request failed", code="NETWORK_ERROR") from error
        if not isinstance(result, dict):
            raise ExaError("Exa response must be a JSON object", code="INVALID_RESPONSE")
        return result


def execute_query(
    run: Run,
    query_id: str,
    *,
    transport: Any | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    timeout: float = 30,
) -> dict[str, Any]:
    """Execute exactly one saved plan row and persist attempts plus one final status."""
    if not isinstance(query_id, str):
        raise TypeError("query_id must be a string from the saved query plan")
    from .context_mode import require_context_preflight

    require_context_preflight(run)
    row = require_plan_row(run.path / "query-plan.jsonl", query_id)
    payload = build_search_payload(row)
    client = transport if transport is not None else UrllibTransport()

    lock_dir = run.path / ".query-locks"
    lock_dir.mkdir(exist_ok=True)
    lock_path = lock_dir / f"{query_id}.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise RuntimeError(f"query is already executing: {query_id}") from error
    os.close(descriptor)
    try:
        from .evidence import read_jsonl

        if any(row.get("query_id") == query_id for row in read_jsonl(run.path / "query-execution.jsonl")):
            raise RuntimeError(f"query is already finalized: {query_id}")
        if any(row.get("query_id") == query_id for row in read_jsonl(run.path / "query-attempts.jsonl")):
            raise RuntimeError(f"query already has persisted attempts: {query_id}")
        return _execute_attempts(run, query_id, payload, client=client, sleeper=sleeper, timeout=timeout)
    finally:
        lock_path.unlink(missing_ok=True)


def _execute_attempts(
    run: Run,
    query_id: str,
    payload: dict[str, Any],
    *,
    client: Any,
    sleeper: Callable[[float], None],
    timeout: float,
) -> dict[str, Any]:

    from .evidence import record_exa_response, record_final_execution, record_query_attempt

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.post(SEARCH_URL, payload, timeout=timeout)
        except TransientExaError as error:
            record_query_attempt(run, query_id=query_id, attempt=attempt, request=payload, status="transient_error", error_code=error.code)
            if attempt == MAX_ATTEMPTS:
                record_final_execution(run, query_id=query_id, final_attempt=attempt, status="failed", error_code=error.code)
                raise
            sleeper(2 ** (attempt - 1))
        except CreditsExhaustedError as error:
            record_query_attempt(run, query_id=query_id, attempt=attempt, request=payload, status="credits_exhausted", error_code=error.code)
            record_final_execution(run, query_id=query_id, final_attempt=attempt, status="credits_exhausted", error_code=error.code)
            raise
        except AuthenticationExaError as error:
            record_query_attempt(run, query_id=query_id, attempt=attempt, request=payload, status="authentication_error", error_code=error.code)
            record_final_execution(run, query_id=query_id, final_attempt=attempt, status="blocked", error_code=error.code)
            raise
        except ExaError as error:
            record_query_attempt(run, query_id=query_id, attempt=attempt, request=payload, status="error", error_code=error.code)
            record_final_execution(run, query_id=query_id, final_attempt=attempt, status="failed", error_code=error.code)
            raise
        else:
            try:
                response = _validate_search_response(response)
            except ExaError as error:
                record_query_attempt(
                    run,
                    query_id=query_id,
                    attempt=attempt,
                    request=payload,
                    status="error",
                    error_code=error.code,
                )
                record_final_execution(
                    run,
                    query_id=query_id,
                    final_attempt=attempt,
                    status="failed",
                    error_code=error.code,
                )
                raise
            record_query_attempt(run, query_id=query_id, attempt=attempt, request=payload, status="success", response=response)
            record_exa_response(run, query_id, response, attempt=attempt, request=payload, finalize=False)
            results = response.get("results", [])
            record_final_execution(
                run,
                query_id=query_id,
                final_attempt=attempt,
                status="completed" if results else "zero_results",
                result_count=len(results) if isinstance(results, list) else 0,
            )
            return response

    raise AssertionError("unreachable")
