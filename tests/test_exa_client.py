from __future__ import annotations

import unittest

from ai_mapper_agent.exa import build_search_payload


class ExaClientTests(unittest.TestCase):
    def test_payload_uses_the_planned_auto_request_without_summary(self) -> None:
        payload = build_search_payload(
            {"query": "China AI", "type": "auto", "num_results": 10, "start_published_date": "2026-07-21", "end_published_date": "2026-08-19"}
        )
        self.assertEqual(payload["type"], "auto")
        self.assertEqual(payload["numResults"], 10)
        self.assertEqual(payload["startPublishedDate"], "2026-07-21")
        self.assertEqual(payload["contents"], {"highlights": True})
        self.assertNotIn("summary", payload["contents"])


if __name__ == "__main__":
    unittest.main()
