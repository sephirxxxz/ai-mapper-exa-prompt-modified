#!/usr/bin/env python3
"""Preflight checks for ai-mapper runs.

This script checks local Elsewhere key presence and, when requested, Elsewhere API availability.
Exa/context-mode are MCP tool-surface checks, so pass their observed status from Main Codex.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def read_key() -> tuple[str, str]:
    env_key = os.environ.get("ELSEWHERE_KEY", "").strip()
    if env_key:
        return env_key, "ELSEWHERE_KEY"
    path = Path.home() / ".config" / "elsewhere" / "key"
    if path.exists():
        return path.read_text(encoding="utf-8").strip(), str(path)
    return "", "missing"


def check_elsewhere(skip_network: bool, timeout: float) -> dict[str, object]:
    key, source = read_key()
    result: dict[str, object] = {
        "key_source": source,
        "key_present": bool(key),
        "key_prefix_valid": key.startswith("els_live_") if key else False,
        "status": "missing_key" if not key else "not_checked",
    }
    if not key:
        return result
    if not key.startswith("els_live_"):
        result["status"] = "invalid_key_prefix"
        return result
    if skip_network:
        result["status"] = "key_present_not_checked"
        return result

    query = urllib.parse.urlencode({"q": "融资", "k": "1", "recency": "prefer"})
    req = urllib.request.Request(
        f"https://elsewhere.news/api/v1/search/chunks?{query}",
        headers={"Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        result["status"] = "available"
        result["http_status"] = 200
        result["sample_count"] = len(payload.get("chunks", [])) if isinstance(payload, dict) else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        result["http_status"] = exc.code
        result["body_preview"] = body
        if exc.code == 429 and "quota_exceeded" in body:
            result["status"] = "quota_exhausted"
        elif exc.code == 429:
            result["status"] = "rate_limited"
        elif exc.code in {401, 403}:
            result["status"] = "auth_error"
        else:
            result["status"] = "error"
    except Exception as exc:  # noqa: BLE001 - preflight should classify, not crash.
        result["status"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="ai-mapper preflight")
    parser.add_argument("--skip-network", action="store_true", help="Only check local key/config state.")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--exa-status", choices=["available", "unavailable", "unknown"], default="unknown")
    parser.add_argument("--context-mode-status", choices=["available", "unavailable", "unknown"], default="unknown")
    parser.add_argument("--run-mode", choices=["adaptive standard scan", "deep map", "blocked"], default="adaptive standard scan")
    args = parser.parse_args()

    elsewhere = check_elsewhere(args.skip_network, args.timeout)
    if args.exa_status == "unavailable":
        completeness = "blocked"
    elif elsewhere["status"] == "available":
        completeness = "complete_candidate"
    elif elsewhere["status"] == "key_present_not_checked":
        completeness = "preflight_pending"
    elif args.exa_status == "available":
        completeness = "degraded / Exa-only"
    else:
        completeness = "preflight_pending"

    print(json.dumps({
        "run_mode": args.run_mode,
        "completeness_preflight": completeness,
        "elsewhere": elsewhere,
        "exa_status": args.exa_status,
        "context_mode_status": args.context_mode_status,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
