"""Lightweight process-memory request instrumentation (diagnostics only).

Context: the Render free instance has shown failures that look like memory
pressure. This module exists to observe per-request resident-set-size (RSS)
behaviour in production so the hypothesis can be confirmed or rejected from
logs alone.

Deliberate constraints (this is diagnostics, not optimisation):
  * RSS is read from Linux ``/proc/self/status`` (``VmRSS``). No profiler, no
    ``tracemalloc``, no ``psutil`` — just one small synchronous file read.
  * The middleware is pure ASGI: the response is never buffered, copied or
    rewritten, so a request behaves identically with or without it.
  * Logging only. No public memory/debug endpoint is exposed anywhere.
  * Only the expensive application route families are instrumented; ``/health``
    and every other route pass through completely untouched and unlogged.

Failure policy: instrumentation must never affect a request. Missing or
unparsable ``/proc`` data degrades to ``NA`` rather than raising, which also
keeps the module usable on non-Linux development machines.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

#: procfs file that reports the process resident set size.
STATUS_PATH = "/proc/self/status"

#: Route families worth observing: the geospatial/hydraulic request paths.
#: Everything else (notably ``/health``) is intentionally exempt.
INSTRUMENTED_PREFIXES: tuple[str, ...] = (
    "/api/delhi",
    "/flood",
    "/routing",
    "/rainfall",
)

#: Query strings are echoed only when short and free of obvious secret keys.
MAX_LOGGED_QUERY_CHARS = 80
_SENSITIVE_QUERY_MARKERS: tuple[str, ...] = (
    "token",
    "secret",
    "password",
    "passwd",
    "auth",
    "api_key",
    "apikey",
    "access_key",
    "signature",
    "credential",
    "session",
    "key=",
    "sig=",
)

#: Placeholder emitted whenever RSS cannot be determined.
NA = "NA"


def read_vm_rss_mb(status_path: str = STATUS_PATH) -> Optional[float]:
    """Return this process's ``VmRSS`` in megabytes, or ``None`` if unknown.

    ``/proc/self/status`` reports ``VmRSS:     123456 kB``. Returns ``None``
    when the file is absent (non-Linux host), unreadable, or malformed, so a
    caller can always treat a missing value as "not measurable" rather than
    having to handle an exception mid-request.
    """
    try:
        with open(status_path, encoding="ascii", errors="replace") as handle:
            for line in handle:
                if line.startswith("VmRSS:"):
                    fields = line.split()
                    if len(fields) < 2:
                        return None
                    return round(int(fields[1]) / 1024.0, 2)
    except (OSError, ValueError):
        return None
    return None


@dataclass(frozen=True)
class MemorySample:
    """One RSS observation, bound to the request path that triggered it."""

    rss_mb: Optional[float]
    path: str
    timestamp: str

    def as_field(self) -> str:
        """Render the RSS value for a log line (``NA`` when unmeasurable)."""
        return NA if self.rss_mb is None else f"{self.rss_mb:.2f}"


def sample_memory(path: str, status_path: str = STATUS_PATH) -> MemorySample:
    """Capture ``rss_mb``, ``path`` and an ISO-8601 UTC ``timestamp``."""
    return MemorySample(
        rss_mb=read_vm_rss_mb(status_path),
        path=path,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    )


def is_instrumented(
    path: str, prefixes: Iterable[str] = INSTRUMENTED_PREFIXES
) -> bool:
    """True when ``path`` belongs to an instrumented route family.

    Matching is segment-aware: ``/flood`` and ``/flood/forecast`` match the
    ``/flood`` prefix, while an unrelated path such as ``/floodplain`` does not.
    """
    return any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)


def format_query_suffix(scope: Any) -> str:
    """Return a safe `` query=...`` suffix, or ``""`` when there is nothing to add.

    Query strings are included only when they are short and contain no
    token-like keys. Long or suspicious queries are reported as omitted so the
    log line still shows that parameters existed without leaking their values.
    """
    raw = scope.get("query_string") or b""
    if not raw:
        return ""
    try:
        text = raw.decode("latin-1")
    except Exception:  # pragma: no cover - latin-1 decoding cannot realistically fail
        return ""
    if len(text) > MAX_LOGGED_QUERY_CHARS:
        return " query=<omitted:long>"
    lowered = text.lower()
    if any(marker in lowered for marker in _SENSITIVE_QUERY_MARKERS):
        return " query=<omitted:sensitive>"
    return f" query={text}"


def _delta_field(before: MemorySample, after: MemorySample) -> str:
    """Signed RSS change across the request, or ``NA`` if either side is unknown."""
    if before.rss_mb is None or after.rss_mb is None:
        return NA
    return f"{after.rss_mb - before.rss_mb:+.2f}"


class RequestMemoryLogMiddleware:
    """Pure-ASGI middleware that logs RSS around selected requests.

    Implemented as raw ASGI rather than ``BaseHTTPMiddleware`` so the response
    body is never buffered: only the status code on ``http.response.start`` is
    read, and every message is forwarded unchanged. Non-HTTP scopes (WebSocket,
    lifespan) are passed straight through.
    """

    def __init__(
        self,
        app: Any,
        prefixes: Iterable[str] = INSTRUMENTED_PREFIXES,
        status_path: str = STATUS_PATH,
        clock: Any = time.perf_counter,
    ) -> None:
        self.app = app
        self.prefixes = tuple(prefixes)
        self.status_path = status_path
        self._clock = clock

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not is_instrumented(path, self.prefixes):
            await self.app(scope, receive, send)
            return

        query_suffix = format_query_suffix(scope)
        before = sample_memory(path, self.status_path)
        logger.info(
            "REQUEST_START path=%s rss_mb=%s%s",
            path,
            before.as_field(),
            query_suffix,
        )

        started = self._clock()
        status_seen: dict[str, Any] = {"status": None}

        async def send_wrapper(message: Any) -> None:
            if message.get("type") == "http.response.start":
                status_seen["status"] = message.get("status")
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            self._log_end(path, "EXCEPTION", started, before, query_suffix)
            raise

        self._log_end(path, status_seen["status"], started, before, query_suffix)

    def _log_end(
        self,
        path: str,
        status: Any,
        started: float,
        before: MemorySample,
        query_suffix: str,
    ) -> None:
        duration_ms = (self._clock() - started) * 1000.0
        after = sample_memory(path, self.status_path)
        logger.info(
            "REQUEST_END path=%s status=%s duration_ms=%.1f "
            "rss_before_mb=%s rss_after_mb=%s rss_delta_mb=%s%s",
            path,
            status,
            duration_ms,
            before.as_field(),
            after.as_field(),
            _delta_field(before, after),
            query_suffix,
        )
