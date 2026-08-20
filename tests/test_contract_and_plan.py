from __future__ import annotations

from collections import Counter
from datetime import date
import unittest

from ai_mapper_agent.contract import LANE_BUDGETS, RUN_SCHEMA_VERSION
from ai_mapper_agent.plan import build_query_plan, validate_query_plan


class ContractAndPlanTests(unittest.TestCase):
    def test_contract_exposes_locked_v2_invariants(self) -> None:
        self.assertEqual(RUN_SCHEMA_VERSION, 2)
        self.assertEqual(
            LANE_BUDGETS,
            {"A-dev": 10, "B-content": 8, "C-funding": 14, "D-academic": 8},
        )

    def test_fixed_query_plan_has_exact_lane_allocation_and_unique_ids(self) -> None:
        rows = build_query_plan(topic=None, run_date=date(2026, 8, 19))

        self.assertEqual(len(rows), 40)
        self.assertEqual(
            Counter(row["lane"] for row in rows),
            {"A-dev": 10, "B-content": 8, "C-funding": 14, "D-academic": 8},
        )
        self.assertEqual(
            {row["query_id"] for row in rows},
            {f"q{index:02d}" for index in range(1, 41)},
        )
        self.assertTrue(validate_query_plan(rows).ok)

    def test_plan_uses_one_exa_mode_and_30_day_published_window(self) -> None:
        rows = build_query_plan(topic=None, run_date=date(2026, 8, 19))

        for row in rows:
            self.assertEqual(row["type"], "auto")
            self.assertEqual(row["num_results"], 10)
            self.assertEqual(row["start_published_date"], "2026-07-21T00:00:00+08:00")
            self.assertEqual(row["end_published_date"], "2026-08-20T00:00:00+08:00")
            self.assertNotIn("deep", row["query"].lower())

    def test_optional_topic_is_a_filter_not_an_extra_query_or_mode(self) -> None:
        rows = build_query_plan(topic="具身智能", run_date=date(2026, 8, 19))

        self.assertEqual(len(rows), 40)
        self.assertTrue(all("具身智能" in row["query"] for row in rows))
        self.assertTrue(all(row["type"] == "auto" for row in rows))


if __name__ == "__main__":
    unittest.main()
