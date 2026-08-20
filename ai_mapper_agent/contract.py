from __future__ import annotations

RUN_SCHEMA_VERSION = 2
LANE_BUDGETS = {
    "A-dev": 10,
    "B-content": 8,
    "C-funding": 14,
    "D-academic": 8,
}
TOTAL_QUERY_COUNT = sum(LANE_BUDGETS.values())
MAX_RESULTS_PER_QUERY = 10
MAX_FETCHED_PAGES = 60
TERMINAL_QUERY_STATUSES = frozenset(
    {"completed", "zero_results", "failed", "blocked", "credits_exhausted"}
)
RUN_STATUSES = frozenset({"in_progress", "complete", "partial", "blocked"})
