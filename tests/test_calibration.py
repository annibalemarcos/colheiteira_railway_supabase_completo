from __future__ import annotations

from core.scorer import Scorer
from server.app import bulk_settings_from_payload


def test_bulk_concurrency_defaults_to_one_and_is_clamped():
    assert bulk_settings_from_payload({"settings": {}})["concurrency"] == 1
    assert bulk_settings_from_payload({"settings": {"concurrency": 2}})["concurrency"] == 2
    assert bulk_settings_from_payload({"settings": {"concurrency": 99}})["concurrency"] == 3
    assert bulk_settings_from_payload({"settings": {"concurrency": 0}})["concurrency"] == 1


def test_failed_heavy_plugin_makes_ranking_inconclusive():
    plugins = {
        "lighthouse": {"status": "error", "score": 0, "peso": 2.4},
        "seo": {"status": "ok", "score": 85, "peso": 1.5},
        "links": {"status": "ok", "score": 90, "peso": 1.3},
        "imagens": {"status": "ok", "score": 90, "peso": 1.2},
        "social_media": {"status": "ok", "score": 50, "peso": 0.3},
        "ortografia": {"status": "not_applicable", "score": 100, "peso": 0.7},
    }

    result = Scorer(80).calculate_analysis(plugins)

    assert result["rankable"] is False
    assert result["analysis_status"] == "partial"
    assert result["coverage"] < 80
    assert result["ranking"].startswith("Inconclusivo")


def test_not_applicable_plugin_does_not_reduce_coverage():
    plugins = {
        "seo": {"status": "ok", "score": 80, "peso": 1.5},
        "ortografia": {"status": "not_applicable", "score": 100, "peso": 0.7},
    }

    result = Scorer(80).calculate_analysis(plugins)

    assert result["coverage"] == 100
    assert result["rankable"] is True
