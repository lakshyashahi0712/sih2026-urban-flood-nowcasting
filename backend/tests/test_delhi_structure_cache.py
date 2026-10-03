"""Disk-artifact tests for the Delhi structure cache.

The artifact is only safe while a stale pickle can never be served, so these
pin the invalidation contract rather than the speed: matching key loads, any
key change rebuilds, an unreadable artifact rebuilds, and a disabled cache
never touches disk.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.domain.delhi import structure_cache as sc


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(sc, "CACHE_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(sc, "_ENABLED", True)
    monkeypatch.setattr(sc, "_WRITES", True)
    monkeypatch.setattr(sc, "_process_key", "key-v1")
    monkeypatch.setattr(sc, "_status", {})
    return tmp_path / "artifacts"


class Payload:
    def __init__(self, tag):
        self.tag = tag


def make_builder(counter):
    def build():
        counter.append(1)
        return Payload("built")

    return build


def test_first_call_builds_and_writes(cache):
    counter = []
    loaded = sc.disk_artifact("thing")(make_builder(counter))()
    assert loaded.tag == "built"
    assert counter == [1]
    assert sc.status()["thing"] == "built"
    assert (cache / "thing.pkl").exists()
    assert (cache / "thing.key").read_text(encoding="utf-8") == "key-v1"


def test_matching_key_loads_without_rebuilding(cache):
    counter = []
    builder = sc.disk_artifact("thing")(make_builder(counter))
    builder()
    counter.clear()
    sc._status.clear()
    again = builder()
    assert again.tag == "built"
    assert counter == []
    assert sc.status()["thing"] == "loaded"


def test_changed_key_rebuilds(cache):
    counter = []
    builder = sc.disk_artifact("thing")(make_builder(counter))
    builder()
    sc._process_key = "key-v2"
    result = builder()
    assert counter == [1, 1]
    assert result.tag == "built"


def test_corrupt_artifact_falls_back_to_building(cache):
    cache.mkdir(parents=True)
    (cache / "thing.pkl").write_bytes(b"not a pickle")
    (cache / "thing.key").write_text("key-v1", encoding="utf-8")
    counter = []
    result = sc.disk_artifact("thing")(make_builder(counter))()
    assert result.tag == "built"
    assert counter == [1]


def test_disabled_cache_never_touches_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(sc, "CACHE_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(sc, "_ENABLED", False)
    monkeypatch.setattr(sc, "_WRITES", False)
    monkeypatch.setattr(sc, "_process_key", "key-v1")
    monkeypatch.setattr(sc, "_status", {})
    counter = []
    builder = sc.disk_artifact("thing")(make_builder(counter))
    builder()
    builder()
    assert counter == [1, 1]
    assert not (tmp_path / "artifacts").exists()


def test_write_disabled_does_not_create_the_directory(cache, monkeypatch):
    monkeypatch.setattr(sc, "_WRITES", False)
    counter = []
    result = sc.disk_artifact("thing")(make_builder(counter))()
    assert result.tag == "built"
    assert not cache.exists()


def test_key_changes_when_domain_source_changes(tmp_path, monkeypatch):
    root = tmp_path / "domain"
    root.mkdir()
    (root / "model.py").write_text("X = 1\n", encoding="utf-8")
    monkeypatch.setattr(sc, "_DOMAIN_ROOT", root)
    monkeypatch.setattr(sc, "_data_files", lambda: [])
    first = sc.cache_key()
    (root / "model.py").write_text("X = 2\n", encoding="utf-8")
    assert sc.cache_key() != first


def test_key_changes_when_a_data_file_changes(tmp_path, monkeypatch):
    root = tmp_path / "domain"
    root.mkdir()
    data = tmp_path / "dem.tif"
    data.write_bytes(b"elevations")
    monkeypatch.setattr(sc, "_DOMAIN_ROOT", root)
    monkeypatch.setattr(sc, "_data_files", lambda: [data])
    first = sc.cache_key()
    data.write_bytes(b"other values")
    assert sc.cache_key() != first
