from __future__ import annotations

import unittest

from ai_mapper_agent.web import validate_fetch_url


class WebSafetyTests(unittest.TestCase):
    def test_accepts_public_http_urls(self) -> None:
        self.assertEqual(
            validate_fetch_url("https://example.test/a#fragment", resolver=lambda _: ["8.8.8.8"]),
            "https://example.test/a",
        )

    def test_rejects_hostname_that_resolves_to_a_private_address(self) -> None:
        with self.assertRaisesRegex(ValueError, "public"):
            validate_fetch_url("https://alias.test/x", resolver=lambda _: ["127.0.0.1"])

    def test_rejects_local_private_and_metadata_destinations(self) -> None:
        for value in (
            "file:///etc/passwd",
            "http://localhost/admin",
            "http://127.0.0.1/admin",
            "http://10.0.0.1/admin",
            "http://169.254.169.254/latest/meta-data",
            "http://metadata.google.internal/computeMetadata/v1/",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "public"):
                    validate_fetch_url(value, resolver=lambda _: ["8.8.8.8"])


if __name__ == "__main__":
    unittest.main()
