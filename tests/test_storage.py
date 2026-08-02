from __future__ import annotations

from pathlib import Path

from core.storage import ResultStorage


def sample_result() -> dict:
    return {
        "url": "https://example.com",
        "inicio": "2026-08-01T10:00:00",
        "fim": "2026-08-01T10:01:00",
        "plugins": {"seo": {"status": "ok", "score": 88, "peso": 1}},
        "score_final": 88,
        "ranking": "A",
    }


def test_file_backend_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("STORAGE_BACKEND", "files")
    storage = ResultStorage(tmp_path, tmp_path / "output")

    storage.save(sample_result(), filename="resultado.json")

    assert storage.latest()["score_final"] == 88
    assert storage.get("resultado.json")["url"] == "https://example.com"
    assert storage.history()[0]["file"] == "resultado.json"


def test_database_backend_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("STORAGE_BACKEND", "database")
    monkeypatch.setenv("STORAGE_STRICT", "true")
    storage = ResultStorage(tmp_path, tmp_path / "output")

    saved = storage.save(sample_result(), filename="resultado.json")

    assert saved["storage_id"]
    assert storage.latest()["score_final"] == 88
    assert storage.get("resultado.json")["url"] == "https://example.com"
    assert storage.history()[0]["file"] == "resultado.json"

    storage.clear(include_history=False)
    assert storage.latest() is None
    assert storage.get("resultado.json") is not None

    storage.clear(include_history=True)
    assert storage.history() == []
