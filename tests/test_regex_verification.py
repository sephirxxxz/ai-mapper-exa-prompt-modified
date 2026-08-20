from __future__ import annotations

import unittest

from ai_mapper_agent.verification import verify_regex_claim


class RegexVerificationTests(unittest.TestCase):
    def test_returns_a_bounded_matching_excerpt_for_a_valid_claim_pattern(self) -> None:
        result = verify_regex_claim("Company launched on 2026-08-10 with a public demo.", r"launched on 2026-08-10")

        self.assertTrue(result.matched)
        self.assertIn("launched on 2026-08-10", result.excerpt)

    def test_reports_a_non_match_without_promoting_an_unverified_claim(self) -> None:
        result = verify_regex_claim("Company launched on 2026-08-10.", r"raised \$10m")

        self.assertFalse(result.matched)
        self.assertEqual(result.excerpt, "")


if __name__ == "__main__":
    unittest.main()
