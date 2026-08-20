from __future__ import annotations

import ipaddress
import socket
from typing import Callable, Iterable
from urllib.parse import urlsplit, urlunsplit


_BLOCKED_HOSTS = {"localhost", "metadata.google.internal", "metadata.aws.internal"}


def resolve_host(hostname: str) -> list[str]:
    return sorted({item[4][0] for item in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)})


def _require_public(addresses: Iterable[str]) -> tuple[str, ...]:
    resolved = list(addresses)
    if not resolved:
        raise ValueError("only resolvable public http(s) URLs are allowed")
    for value in resolved:
        try:
            address = ipaddress.ip_address(value)
        except ValueError as error:
            raise ValueError("only public http(s) URLs are allowed") from error
        if not address.is_global:
            raise ValueError("only public http(s) URLs are allowed")
    return tuple(resolved)


def validate_and_resolve_fetch_url(
    value: str,
    *,
    resolver: Callable[[str], Iterable[str]] = resolve_host,
) -> tuple[str, tuple[str, ...]]:
    """Allow only public HTTP(S) URLs before any browser or HTTP fetch is attempted."""
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("only public http(s) URLs are allowed")
    hostname = parsed.hostname.lower()
    if hostname in _BLOCKED_HOSTS or hostname.endswith((".local", ".internal")):
        raise ValueError("only public http(s) URLs are allowed")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        addresses = _require_public([hostname])
    else:
        try:
            addresses = _require_public(resolver(hostname))
        except (OSError, socket.gaierror) as error:
            raise ValueError("only resolvable public http(s) URLs are allowed") from error
    canonical = urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))
    return canonical, addresses


def validate_fetch_url(value: str, *, resolver: Callable[[str], Iterable[str]] = resolve_host) -> str:
    """Allow only public HTTP(S) URLs before any browser or HTTP fetch is attempted."""
    canonical, _ = validate_and_resolve_fetch_url(value, resolver=resolver)
    return canonical
