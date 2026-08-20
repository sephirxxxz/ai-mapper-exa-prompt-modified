from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import importlib
from pathlib import Path
import tempfile
import threading
import time
import unittest
from zoneinfo import ZoneInfo

from ai_mapper_agent.context_mode import ContextPreflightReceipt, record_context_preflight
from ai_mapper_agent.evidence import record_fetch
from ai_mapper_agent.guard import final_guard
from ai_mapper_agent.run import create_run


try:
    fetch_module = importlib.import_module("ai_mapper_agent.fetch")
except ModuleNotFoundError:
    fetch_module = None


NOW = datetime(2026, 8, 19, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
PUBLIC_RESOLVER = lambda _: ["8.8.8.8"]


@dataclass
class FakeResponse:
    status_code: int
    body: bytes = b""
    content_type: str = "text/html; charset=utf-8"
    location: str | None = None

    @property
    def is_redirect(self) -> bool:
        return self.status_code in {301, 302, 303, 307, 308}

    def read(self, limit: int) -> bytes:
        return self.body[:limit]


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.urls: list[str] = []
        self.resolved_addresses: list[tuple[str, ...]] = []

    def get(
        self,
        url: str,
        *,
        timeout: float,
        follow_redirects: bool,
        resolved_addresses: tuple[str, ...],
    ) -> FakeResponse:
        self.urls.append(url)
        self.resolved_addresses.append(resolved_addresses)
        return self.responses.pop(0)


class FailIfCalled:
    def get(
        self,
        url: str,
        *,
        timeout: float,
        follow_redirects: bool,
        resolved_addresses: tuple[str, ...],
    ) -> FakeResponse:
        raise AssertionError("network transport must not be called")


class FetchPipelineTests(unittest.TestCase):
    def _run(self, root: Path):
        run = create_run(root, topic=None, timezone_name="Asia/Shanghai", now=NOW)
        project_dir = run.manifest["agent_root"]
        record_context_preflight(
            run,
            ContextPreflightReceipt(
                doctor_tool="ctx_doctor",
                doctor_ok=True,
                doctor_summary="all required checks passed",
                purge_tool="ctx_purge",
                purge_ok=True,
                purge_scope="project",
                project_dir=project_dir,
                context_dir=str(Path(project_dir) / ".context-mode"),
                started_at="2026-08-19T01:29:00+00:00",
                completed_at="2026-08-19T01:29:02+00:00",
                host_call_ids=("doctor-call-1", "purge-call-1"),
            ),
        )
        return run

    def test_redirect_target_is_revalidated_before_following(self) -> None:
        fetch = getattr(fetch_module, "fetch_public_page", None) if fetch_module else None
        self.assertTrue(callable(fetch), "fetch_public_page must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            transport = FakeTransport([FakeResponse(302, location="http://169.254.169.254/latest")])

            with self.assertRaisesRegex(ValueError, "public"):
                fetch(run, "https://public.test/start", transport=transport, resolver=PUBLIC_RESOLVER)
            self.assertEqual(transport.urls, ["https://public.test/start"])

    def test_successful_fetch_persists_a_hashed_page_and_receipt(self) -> None:
        fetch = getattr(fetch_module, "fetch_public_page", None) if fetch_module else None
        self.assertTrue(callable(fetch), "fetch_public_page must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            body = b"<html><body>public evidence</body></html>"

            receipt = fetch(
                run,
                "https://public.test/page",
                transport=FakeTransport([FakeResponse(200, body=body)]),
                resolver=PUBLIC_RESOLVER,
            )

            saved = run.path / receipt.path
            self.assertEqual(saved.read_bytes(), body)
            self.assertEqual(receipt.content_hash, sha256(body).hexdigest())

    def test_validated_dns_addresses_are_pinned_into_the_transport(self) -> None:
        fetch = getattr(fetch_module, "fetch_public_page", None) if fetch_module else None
        self.assertTrue(callable(fetch), "fetch_public_page must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            transport = FakeTransport([FakeResponse(200, body=b"public")])

            fetch(run, "https://public.test/page", transport=transport, resolver=PUBLIC_RESOLVER)

            self.assertEqual(transport.resolved_addresses, [("8.8.8.8",)])

    def test_guard_rejects_success_without_a_saved_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            record_fetch(
                run,
                url="https://public.test/missing",
                status="success",
                path="pages/missing.html",
                method="browser",
                byte_count=10,
                content_hash=sha256(b"not-saved").hexdigest(),
            )

            self.assertIn("FETCH_ARTIFACT_MISSING", final_guard(run.path).codes)

    def test_guard_rejects_a_page_whose_hash_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            page = run.path / "pages" / "changed.html"
            page.write_bytes(b"changed")
            record_fetch(
                run,
                url="https://public.test/changed",
                status="success",
                path="pages/changed.html",
                method="http",
                byte_count=8,
                content_hash=sha256(b"original").hexdigest(),
            )

            self.assertIn("FETCH_HASH_MISMATCH", final_guard(run.path).codes)

    def test_sixty_first_unique_fetch_is_rejected_before_network(self) -> None:
        fetch = getattr(fetch_module, "fetch_public_page", None) if fetch_module else None
        self.assertTrue(callable(fetch), "fetch_public_page must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            for index in range(60):
                body = f"page-{index}".encode()
                page = run.path / "pages" / f"page-{index}.html"
                page.write_bytes(body)
                record_fetch(
                    run,
                    url=f"https://public.test/{index}",
                    status="success",
                    path=f"pages/page-{index}.html",
                    method="browser",
                    byte_count=len(body),
                    content_hash=sha256(body).hexdigest(),
                )

            with self.assertRaisesRegex(RuntimeError, "FETCH_CAP_REACHED"):
                fetch(
                    run,
                    "https://public.test/61",
                    transport=FailIfCalled(),
                    resolver=PUBLIC_RESOLVER,
                )

    def test_concurrent_reservations_cannot_exceed_sixty_unique_pages(self) -> None:
        reserve = getattr(fetch_module, "_reserve_fetch_slot", None) if fetch_module else None
        self.assertTrue(callable(reserve), "atomic fetch reservation must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            for index in range(59):
                record_fetch(run, url=f"https://public.test/{index}", status="reserved", method="http")

            original_read = fetch_module.read_jsonl

            def slow_read(path):
                rows = original_read(path)
                if path.name == "fetches.jsonl":
                    time.sleep(0.05)
                return rows

            fetch_module.read_jsonl = slow_read
            outcomes: list[str] = []

            def attempt(url: str) -> None:
                try:
                    reserve(run, url, method="http")
                    outcomes.append("reserved")
                except RuntimeError as error:
                    outcomes.append(str(error))

            try:
                threads = [
                    threading.Thread(target=attempt, args=(f"https://public.test/new-{index}",))
                    for index in range(2)
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(timeout=2)
            finally:
                fetch_module.read_jsonl = original_read

            self.assertFalse(any(thread.is_alive() for thread in threads))
            self.assertEqual(outcomes.count("reserved"), 1)
            self.assertEqual(outcomes.count("FETCH_CAP_REACHED"), 1)

    def test_invalid_browser_artifact_does_not_consume_a_retryable_url(self) -> None:
        record_browser = getattr(fetch_module, "record_browser_fetch", None) if fetch_module else None
        self.assertTrue(callable(record_browser), "record_browser_fetch must exist")
        with tempfile.TemporaryDirectory() as temp:
            run = self._run(Path(temp))
            with self.assertRaisesRegex(ValueError, "artifact is missing"):
                record_browser(run, "https://public.test/project", "pages/missing.html", resolver=PUBLIC_RESOLVER)
            page = run.path / "pages" / "missing.html"
            page.write_text("recovered", encoding="utf-8")
            receipt = record_browser(run, "https://public.test/project", "pages/missing.html", resolver=PUBLIC_RESOLVER)
            self.assertEqual(receipt.status, "success")


if __name__ == "__main__":
    unittest.main()
