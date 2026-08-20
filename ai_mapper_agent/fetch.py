from __future__ import annotations

from dataclasses import dataclass
import fcntl
from hashlib import sha256
import http.client
from pathlib import Path
import socket
import ssl
from typing import Any, Callable, Iterable
from urllib.parse import urljoin, urlsplit

from .context_mode import require_context_preflight
from .contract import MAX_FETCHED_PAGES
from .evidence import read_jsonl, record_fetch
from .run import Run
from .web import resolve_host, validate_and_resolve_fetch_url, validate_fetch_url


MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3


@dataclass(frozen=True)
class FetchReceipt:
    url: str
    method: str
    status: str
    fetched_at: str
    path: str
    byte_count: int
    content_hash: str
    reason: str | None = None


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: bytes
    content_type: str
    location: str | None

    @property
    def is_redirect(self) -> bool:
        return self.status_code in {301, 302, 303, 307, 308}

    def read(self, limit: int) -> bytes:
        return self.body[:limit]


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, hostname: str, address: str, *, port: int, timeout: float) -> None:
        super().__init__(hostname, port=port, timeout=timeout)
        self._pinned_address = address

    def connect(self) -> None:
        self.sock = self._create_connection(
            (self._pinned_address, self.port), self.timeout, self.source_address
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, hostname: str, address: str, *, port: int, timeout: float) -> None:
        super().__init__(hostname, port=port, timeout=timeout, context=ssl.create_default_context())
        self._pinned_address = address

    def connect(self) -> None:
        self.sock = self._create_connection(
            (self._pinned_address, self.port), self.timeout, self.source_address
        )
        if self._tunnel_host:
            self._tunnel()
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


class PinnedHttpTransport:
    def get(
        self,
        url: str,
        *,
        timeout: float,
        follow_redirects: bool,
        resolved_addresses: tuple[str, ...],
    ) -> HttpResponse:
        if follow_redirects:
            raise ValueError("redirects must be followed by fetch_public_page")
        parsed = urlsplit(url)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        last_error: OSError | None = None
        for address in resolved_addresses:
            connection_type = _PinnedHTTPSConnection if parsed.scheme == "https" else _PinnedHTTPConnection
            connection = connection_type(parsed.hostname or "", address, port=port, timeout=timeout)
            try:
                connection.request("GET", target, headers={"Host": parsed.netloc, "Accept": "text/html,text/plain,*/*;q=0.1"})
                response = connection.getresponse()
                return HttpResponse(
                    status_code=response.status,
                    body=response.read(MAX_PAGE_BYTES + 1),
                    content_type=response.getheader("Content-Type", "application/octet-stream"),
                    location=response.getheader("Location"),
                )
            except OSError as error:
                last_error = error
            finally:
                connection.close()
        raise OSError("could not connect to any validated public address") from last_error


def _reserve_fetch_slot(run: Run, canonical_url: str, *, method: str) -> None:
    lock_path = run.path / ".fetch-reservation.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            rows = read_jsonl(run.path / "fetches.jsonl")
            occupied = {row.get("url") for row in rows if row.get("status") in {"reserved", "success"}}
            if canonical_url in occupied:
                raise RuntimeError("FETCH_ALREADY_RECORDED")
            if len(occupied) >= MAX_FETCHED_PAGES:
                raise RuntimeError("FETCH_CAP_REACHED")
            record_fetch(run, url=canonical_url, status="reserved", method=method)
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _page_extension(content_type: str) -> str:
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type in {"text/html", "application/xhtml+xml"}:
        return ".html"
    if media_type.startswith("text/"):
        return ".txt"
    return ".bin"


def fetch_public_page(
    run: Run,
    url: str,
    *,
    transport: Any | None = None,
    resolver: Callable[[str], Iterable[str]] = resolve_host,
    timeout: float = 15,
) -> FetchReceipt:
    """Fetch one bounded public page, revalidating every redirect and saving proof."""
    require_context_preflight(run)
    canonical, resolved_addresses = validate_and_resolve_fetch_url(url, resolver=resolver)
    _reserve_fetch_slot(run, canonical, method="http")
    client = transport if transport is not None else PinnedHttpTransport()
    current = canonical
    try:
        response = client.get(
            current,
            timeout=timeout,
            follow_redirects=False,
            resolved_addresses=resolved_addresses,
        )
        redirects = 0
        while response.is_redirect:
            if redirects >= MAX_REDIRECTS or not response.location:
                raise ValueError("redirect limit exceeded or Location is missing")
            current, resolved_addresses = validate_and_resolve_fetch_url(
                urljoin(current, response.location), resolver=resolver
            )
            redirects += 1
            response = client.get(
                current,
                timeout=timeout,
                follow_redirects=False,
                resolved_addresses=resolved_addresses,
            )
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f"page fetch failed with HTTP {response.status_code}")
        body = response.read(MAX_PAGE_BYTES + 1)
        if len(body) > MAX_PAGE_BYTES:
            raise ValueError("page exceeds byte limit")
        content_hash = sha256(body).hexdigest()
        filename = sha256(current.encode("utf-8")).hexdigest()[:20] + _page_extension(response.content_type)
        relative_path = str(Path("pages") / filename)
        page_path = run.path / relative_path
        page_path.write_bytes(body)
        record_fetch(
            run,
            url=current,
            status="success",
            path=relative_path,
            method="http",
            byte_count=len(body),
            content_hash=content_hash,
        )
        saved = read_jsonl(run.path / "fetches.jsonl")[-1]
        return FetchReceipt(
            url=saved["url"],
            method=saved["method"],
            status=saved["status"],
            fetched_at=saved["fetched_at"],
            path=saved["path"],
            byte_count=saved["byte_count"],
            content_hash=saved["content_hash"],
        )
    except Exception as error:
        record_fetch(run, url=current, status="failed", method="http", reason=f"{type(error).__name__}: {error}")
        raise


def record_browser_fetch(
    run: Run,
    url: str,
    page_path: str,
    *,
    resolver: Callable[[str], Iterable[str]] = resolve_host,
) -> FetchReceipt:
    """Record a browser-fetched page only when it is a safe run-local artifact."""
    require_context_preflight(run)
    canonical = validate_fetch_url(url, resolver=resolver)
    relative = Path(page_path)
    pages_root = (run.path / "pages").resolve()
    resolved = (run.path / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not resolved.is_relative_to(pages_root):
        raise ValueError("browser page path must be run-relative under pages/")
    if not resolved.is_file():
        raise ValueError("browser page artifact is missing")
    body = resolved.read_bytes()
    if len(body) > MAX_PAGE_BYTES:
        raise ValueError("page exceeds byte limit")
    _reserve_fetch_slot(run, canonical, method="browser")
    content_hash = sha256(body).hexdigest()
    record_fetch(
        run,
        url=canonical,
        status="success",
        path=str(relative),
        method="browser",
        byte_count=len(body),
        content_hash=content_hash,
    )
    saved = read_jsonl(run.path / "fetches.jsonl")[-1]
    return FetchReceipt(
        url=saved["url"],
        method=saved["method"],
        status=saved["status"],
        fetched_at=saved["fetched_at"],
        path=saved["path"],
        byte_count=saved["byte_count"],
        content_hash=saved["content_hash"],
    )
