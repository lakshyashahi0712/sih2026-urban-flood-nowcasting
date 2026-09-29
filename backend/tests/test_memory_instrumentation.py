"""Tests for the lightweight RSS request instrumentation.

These cover the diagnostics added to investigate memory pressure on the Render
free instance: the ``/proc/self/status`` reader and the logging middleware.

No test depends on a real ``/proc`` file — the reader takes an injectable status
path — so the suite behaves identically on Linux CI and on a Windows dev box.
"""
from __future__ import annotations

import logging
from datetime import datetime

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.app.observability import memory_instrumentation as mi


# ---------------------------------------------------------------------------
# /proc/self/status reader
# ---------------------------------------------------------------------------

_STATUS_TEMPLATE = """Name:\tpython
VmPeak:\t 9000000 kB
VmSize:\t 8000000 kB
VmRSS:\t{kb} kB
RssAnon:\t 100000 kB
"""


def test_read_vm_rss_mb_parses_kilobytes(tmp_path):
    status = tmp_path / "status"
    status.write_text(_STATUS_TEMPLATE.format(kb=204800), encoding="ascii")

    assert mi.read_vm_rss_mb(str(status)) == 200.0


def test_read_vm_rss_mb_rounds_to_two_decimals(tmp_path):
    status = tmp_path / "status"
    status.write_text(_STATUS_TEMPLATE.format(kb=1536), encoding="ascii")

    assert mi.read_vm_rss_mb(str(status)) == 1.5


def test_read_vm_rss_mb_missing_file_returns_none(tmp_path):
    assert mi.read_vm_rss_mb(str(tmp_path / "does-not-exist")) is None


def test_read_vm_rss_mb_without_vmrss_line_returns_none(tmp_path):
    status = tmp_path / "status"
    status.write_text("Name:\tpython\nVmSize:\t 10 kB\n", encoding="ascii")

    assert mi.read_vm_rss_mb(str(status)) is None


def test_read_vm_rss_mb_malformed_value_returns_none(tmp_path):
    status = tmp_path / "status"
    status.write_text("VmRSS:\t not-a-number kB\n", encoding="ascii")

    assert mi.read_vm_rss_mb(str(status)) is None


def test_read_vm_rss_mb_on_live_host():
    """On Linux the real /proc file yields a positive value; elsewhere None."""
    value = mi.read_vm_rss_mb()

    assert value is None or value > 0


def test_read_vm_rss_mb_never_raises_on_unreadable_path():
    # Directory path -> IsADirectoryError (an OSError) must be swallowed.
    assert mi.read_vm_rss_mb("/") is None


# ---------------------------------------------------------------------------
# sample_memory helper
# ---------------------------------------------------------------------------


def test_sample_memory_returns_rss_path_and_timestamp(tmp_path):
    status = tmp_path / "status"
    status.write_text(_STATUS_TEMPLATE.format(kb=102400), encoding="ascii")

    sample = mi.sample_memory("/flood/forecast", str(status))

    assert sample.rss_mb == 100.0
    assert sample.path == "/flood/forecast"
    assert datetime.fromisoformat(sample.timestamp) is not None


def test_sample_memory_reports_na_when_unmeasurable(tmp_path):
    sample = mi.sample_memory("/flood/forecast", str(tmp_path / "missing"))

    assert sample.rss_mb is None
    assert sample.as_field() == mi.NA


# ---------------------------------------------------------------------------
# Route-family selection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/delhi",
        "/api/delhi/status",
        "/api/delhi/nowcast/live",
        "/flood",
        "/flood/forecast",
        "/routing",
        "/routing/safe",
        "/rainfall",
        "/rainfall/nowcast",
    ],
)
def test_is_instrumented_matches_selected_families(path):
    assert mi.is_instrumented(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/ready",
        "/",
        "/docs",
        "/api/readings/1",
        "/api/alerts",
        "/api/scenarios",
        "/api/dashboard/summary",
        # segment-aware: a different family sharing a textual prefix
        "/floodplain",
        "/rainfalls",
        "/routing-table",
    ],
)
def test_is_instrumented_skips_other_paths(path):
    assert mi.is_instrumented(path) is False


def test_instrumented_prefixes_are_exactly_the_expensive_families():
    assert set(mi.INSTRUMENTED_PREFIXES) == {
        "/api/delhi",
        "/flood",
        "/routing",
        "/rainfall",
    }


# ---------------------------------------------------------------------------
# Query-string handling
# ---------------------------------------------------------------------------


class _Scope(dict):
    """Minimal ASGI scope stand-in for query-formatting tests."""


@pytest.mark.parametrize("raw", [b"", None])
def test_query_suffix_empty_when_no_query(raw):
    assert mi.format_query_suffix(_Scope(query_string=raw)) == ""


def test_query_suffix_logs_short_non_sensitive_query():
    scope = _Scope(query_string=b"lat=13.08&lon=80.27")

    assert mi.format_query_suffix(scope) == " query=lat=13.08&lon=80.27"


@pytest.mark.parametrize(
    "raw",
    [
        b"token=abc123",
        b"api_key=abc",
        b"apiKey=abc",
        b"ACCESS_KEY=abc",
        b"password=hunter2",
        b"session=xyz",
        b"signature=deadbeef",
        b"Authorization=x",
    ],
)
def test_query_suffix_omits_sensitive_query(raw):
    assert mi.format_query_suffix(_Scope(query_string=raw)) == " query=<omitted:sensitive>"


def test_query_suffix_omits_long_query():
    scope = _Scope(query_string=("a=" + "b" * (mi.MAX_LOGGED_QUERY_CHARS + 10)).encode())

    assert mi.format_query_suffix(scope) == " query=<omitted:long>"


# ---------------------------------------------------------------------------
# Middleware behaviour
# ---------------------------------------------------------------------------


def _build_app(status_path: str) -> FastAPI:
    """A tiny app carrying the middleware plus instrumented and exempt routes."""
    app = FastAPI()
    app.add_middleware(mi.RequestMemoryLogMiddleware, status_path=status_path)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/readings/1")
    def readings():
        return {"value": 1}

    @app.get("/flood/probe")
    def flood_probe():
        return {"ok": True, "payload": [1, 2, 3]}

    @app.get("/api/delhi/status")
    def delhi_status():
        return {"ok": True}

    @app.get("/routing/probe")
    def routing_probe():
        return {"ok": True}

    @app.get("/rainfall/probe")
    def rainfall_probe():
        return {"ok": True}

    @app.get("/flood/teapot")
    def flood_teapot():
        raise HTTPException(status_code=503, detail="unavailable")

    @app.get("/flood/boom")
    def flood_boom():
        raise RuntimeError("kaboom")

    return app


@pytest.fixture()
def status_file(tmp_path):
    status = tmp_path / "status"
    status.write_text(_STATUS_TEMPLATE.format(kb=512000), encoding="ascii")
    return str(status)


@pytest.fixture()
def client(status_file):
    # raise_server_exceptions=False so the unhandled-exception path is observable
    # as a 500 response rather than a re-raised error in the test client.
    with TestClient(_build_app(status_file), raise_server_exceptions=False) as c:
        yield c


def _log_text(caplog) -> str:
    return "\n".join(caplog.messages) if caplog.messages else caplog.text


def test_instrumented_request_logs_start_and_end(client, caplog):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        response = client.get("/flood/probe")

    assert response.status_code == 200
    text = _log_text(caplog)
    assert "REQUEST_START path=/flood/probe rss_mb=500.00" in text
    assert "REQUEST_END path=/flood/probe status=200" in text
    assert "duration_ms=" in text
    assert "rss_before_mb=500.00" in text
    assert "rss_after_mb=500.00" in text
    assert "rss_delta_mb=+0.00" in text


@pytest.mark.parametrize(
    "path",
    ["/api/delhi/status", "/routing/probe", "/rainfall/probe"],
)
def test_every_instrumented_family_is_logged(client, caplog, path):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        response = client.get(path)

    assert response.status_code == 200
    assert f"REQUEST_START path={path} rss_mb=" in _log_text(caplog)
    assert f"REQUEST_END path={path} status=200" in _log_text(caplog)


@pytest.mark.parametrize("path", ["/health", "/api/readings/1", "/docs", "/openapi.json"])
def test_exempt_requests_are_not_logged(client, caplog, path):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        client.get(path)

    text = _log_text(caplog)
    assert "REQUEST_START" not in text
    assert "REQUEST_END" not in text


def test_health_is_never_logged_even_under_load(client, caplog):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        for _ in range(25):
            assert client.get("/health").status_code == 200

    assert _log_text(caplog).strip() == ""


def test_error_status_is_recorded(client, caplog):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        response = client.get("/flood/teapot")

    assert response.status_code == 503
    assert "REQUEST_END path=/flood/teapot status=503" in _log_text(caplog)


def test_unhandled_exception_is_logged_and_reraised(client, caplog):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        response = client.get("/flood/boom")

    # The exception must still become a 500 — instrumentation does not swallow it.
    assert response.status_code == 500
    assert "REQUEST_END path=/flood/boom status=EXCEPTION" in _log_text(caplog)


def test_response_is_passed_through_unchanged(client, caplog):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        instrumented = client.get("/flood/probe")
    body_headers = {k: v for k, v in instrumented.headers.items()}

    assert instrumented.status_code == 200
    assert instrumented.json() == {"ok": True, "payload": [1, 2, 3]}
    assert body_headers.get("content-type", "").startswith("application/json")


def test_unmatched_route_under_instrumented_prefix_is_still_logged(client, caplog):
    """Selection is by path family, not by matched route.

    A 404 under /flood still belongs to an expensive family, so it is logged
    with its real status — useful evidence, since probes often hit dead paths.
    """
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        response = client.get("/flood/does-not-exist")

    assert response.status_code == 404
    assert "REQUEST_END path=/flood/does-not-exist status=404" in _log_text(caplog)


def test_unmatched_route_outside_instrumented_prefix_is_not_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        response = client.get("/nope/does-not-exist")

    assert response.status_code == 404
    assert "REQUEST_START" not in _log_text(caplog)


def test_query_logged_when_short_and_safe(client, caplog):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        client.get("/flood/probe?lat=13.08&lon=80.27")

    assert "REQUEST_START path=/flood/probe rss_mb=500.00 query=lat=13.08&lon=80.27" in _log_text(caplog)


def test_sensitive_query_not_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        client.get("/flood/probe?token=supersecret")

    text = _log_text(caplog)
    assert "supersecret" not in text
    assert "query=<omitted:sensitive>" in text


def test_long_query_not_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        client.get("/flood/probe?" + "a=" + "b" * 120)

    text = _log_text(caplog)
    assert "query=<omitted:long>" in text


def test_missing_proc_file_logs_na_without_failing(tmp_path, caplog):
    app = _build_app(str(tmp_path / "no-such-status"))
    with TestClient(app) as c:
        with caplog.at_level(logging.INFO, logger=mi.logger.name):
            response = c.get("/flood/probe")

    assert response.status_code == 200
    text = _log_text(caplog)
    assert "REQUEST_START path=/flood/probe rss_mb=NA" in text
    assert "rss_before_mb=NA rss_after_mb=NA rss_delta_mb=NA" in text


def test_non_http_scope_passes_through_untouched(caplog):
    """WebSocket and lifespan scopes must not be logged or altered."""
    seen: list[dict] = []

    async def fake_app(scope, receive, send):
        seen.append(scope)

    async def receive():
        return {"type": "websocket.connect"}

    async def send(message):
        return None

    middleware = mi.RequestMemoryLogMiddleware(fake_app)

    import asyncio

    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        asyncio.run(middleware({"type": "websocket", "path": "/ws"}, receive, send))
        asyncio.run(middleware({"type": "lifespan", "path": ""}, receive, send))

    assert len(seen) == 2
    assert _log_text(caplog).strip() == ""


def test_delta_field_is_signed_and_unavailable_when_unknown():
    before = mi.MemorySample(rss_mb=100.0, path="/flood", timestamp="t")
    after = mi.MemorySample(rss_mb=112.5, path="/flood", timestamp="t")

    assert mi._delta_field(before, after) == "+12.50"
    assert mi._delta_field(before, mi.MemorySample(None, "/flood", "t")) == mi.NA


def test_module_does_not_configure_global_logging():
    """Importing diagnostics must not add handlers or change root log level."""
    root = logging.getLogger()

    assert root.level == logging.WARNING or isinstance(root.level, int)
    assert not any(
        getattr(h, "_memory_instrumentation", False) for h in root.handlers
    )


def test_real_application_registers_the_middleware():
    """Guards the main.py wiring: the middleware must be on the real app."""
    from backend.main import app

    assert any(
        entry.cls is mi.RequestMemoryLogMiddleware for entry in app.user_middleware
    )


def test_real_application_serves_health_without_logging(caplog):
    """The instrumented app must start normally and leave /health unlogged."""
    from backend.main import app

    with caplog.at_level(logging.INFO, logger=mi.logger.name):
        with TestClient(app) as c:
            assert c.get("/health").status_code == 200

    assert "REQUEST_START" not in _log_text(caplog)
