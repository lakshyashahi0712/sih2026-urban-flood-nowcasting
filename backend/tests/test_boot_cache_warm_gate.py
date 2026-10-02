"""Boot cache warm-up gate and warm order.

The warm thread calls the real model pipelines, so it must never run under
pytest: an earlier import-time check read the environment before pytest had set
PYTEST_CURRENT_TEST, a test that entered ``with TestClient(app)`` started a
genuine warm-up, and that thread appended phantom model runs into whatever test
had monkeypatched the pipeline — order-dependent failures in the V1 cache
suite.

The two surfaces are built one at a time, so which one goes first decides whose
first visitor waits ~50 s longer on Render's 0.1 CPU. That order is operator
input (FLOOD_WARM_ORDER) and is pinned here.
"""

from __future__ import annotations

import contextlib
import sys
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend import main


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in ("FLOOD_WARM_ON_BOOT", "DELHI_WARM_ON_BOOT", "FLOOD_WARM_ORDER"):
        monkeypatch.delenv(var, raising=False)


def test_gate_is_closed_while_pytest_is_running():
    # This assertion executes inside a pytest run, which is exactly the
    # condition the gate must detect.
    assert main._warm_on_boot("FLOOD_WARM_ON_BOOT") is False
    assert main._warm_on_boot("DELHI_WARM_ON_BOOT") is False


def test_startup_does_not_launch_the_warm_thread_under_tests():
    with TestClient(main.app) as client:
        assert client.get("/health").status_code == 200
        names = {t.name for t in threading.enumerate()}
    assert "flood-cache-warm" not in names


@contextlib.contextmanager
def _production_interpreter(monkeypatch):
    """Pretend to be uvicorn: no pytest imported, no pytest env var.

    Applied inside the test body, not as a fixture — pytest re-sets
    PYTEST_CURRENT_TEST for every test phase after fixtures have run, so a
    fixture-scoped delenv is already undone by the time the body executes.
    """
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delitem(sys.modules, "pytest", raising=False)
    yield


def test_gate_is_open_outside_tests(monkeypatch):
    with _production_interpreter(monkeypatch):
        assert main._warm_on_boot("FLOOD_WARM_ON_BOOT") is True
        assert main._warm_on_boot("DELHI_WARM_ON_BOOT") is True


def test_operator_switches_still_turn_it_off(monkeypatch):
    with _production_interpreter(monkeypatch):
        monkeypatch.setenv("FLOOD_WARM_ON_BOOT", "0")
        monkeypatch.setenv("DELHI_WARM_ON_BOOT", "0")
        assert main._warm_on_boot("FLOOD_WARM_ON_BOOT") is False
        assert main._warm_on_boot("DELHI_WARM_ON_BOOT") is False


@pytest.fixture
def warm_calls(monkeypatch):
    """Record which surface actually ran, in order, without building anything."""
    calls: list = []
    monkeypatch.setattr(
        main, "_warm_mumbai_flood_caches", lambda: calls.append("mumbai")
    )
    monkeypatch.setattr(
        main, "_warm_delhi_flood_caches", lambda: calls.append("delhi")
    )
    return calls


def test_launch_surface_warms_first_by_default(monkeypatch, warm_calls):
    with _production_interpreter(monkeypatch):
        main._warm_flood_caches_at_boot()
        assert warm_calls == ["mumbai", "delhi"]


def test_delhi_can_take_the_cpu_first_for_a_delhi_cold_boot(monkeypatch, warm_calls):
    with _production_interpreter(monkeypatch):
        # Case and surrounding spaces are operator input, not code input.
        monkeypatch.setenv("FLOOD_WARM_ORDER", " DELHI ")
        main._warm_flood_caches_at_boot()
        assert warm_calls == ["delhi", "mumbai"]


def test_unknown_warm_order_falls_back_to_the_default(monkeypatch, warm_calls):
    with _production_interpreter(monkeypatch):
        monkeypatch.setenv("FLOOD_WARM_ORDER", "kushak")
        main._warm_flood_caches_at_boot()
        assert warm_calls == ["mumbai", "delhi"]


def test_reordering_does_not_warm_a_switched_off_surface(monkeypatch, warm_calls):
    with _production_interpreter(monkeypatch):
        monkeypatch.setenv("FLOOD_WARM_ORDER", "delhi")
        monkeypatch.setenv("FLOOD_WARM_ON_BOOT", "0")
        main._warm_flood_caches_at_boot()
        assert warm_calls == ["delhi"]
