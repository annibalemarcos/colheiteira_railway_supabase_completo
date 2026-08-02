"""Motor reaproveitável da análise web."""
from __future__ import annotations

import json
import re
import threading
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

from core.config_loader import ConfigLoader
from core.plugin_loader import PluginLoader
from core.scorer import Scorer

ProgressCallback = Optional[Callable[[str, str], None]]
BASE_DIR = Path(__file__).resolve().parent.parent

# Lighthouse/Chromium é o componente mais pesado. Mesmo quando o lote usa
# concorrência 2 ou 3, só uma auditoria Lighthouse roda por processo.
_RESOURCE_LOCKS = {"lighthouse": threading.Lock()}


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        raise ValueError("URL não pode ficar vazia.")
    if not re.match(r"^https?://", url, flags=re.I):
        url = f"https://{url}"
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError("URL inválida. Exemplo correto: https://example.com")
    return url


def _emit(progress: ProgressCallback, message: str, level: str = "info") -> None:
    if progress:
        progress(message, level)


def run_analysis(
    url: str,
    *,
    progress: ProgressCallback = None,
    output_dir: str | Path | None = None,
    save_history: bool = True,
) -> Dict[str, Any]:
    normalized_url = normalize_url(url)
    output_path = Path(output_dir) if output_dir else BASE_DIR / "output"
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path

    _emit(progress, f"Iniciando análise completa de {normalized_url}", "info")

    loader = PluginLoader(str(BASE_DIR / "plugins"))
    plugins = loader.load_all_plugins()
    _emit(progress, f"{len(plugins)} plugin(s) carregado(s).", "success")

    result: Dict[str, Any] = {
        "url": normalized_url,
        "inicio": datetime.now().isoformat(),
        "plugins": {},
    }

    for name, plugin in plugins.items():
        _emit(progress, f"Executando plugin: {name}", "info")
        lock = _RESOURCE_LOCKS.get(name)
        context = lock if lock is not None else nullcontext()
        try:
            if lock is not None and lock.locked():
                _emit(progress, f"{name}: aguardando recurso exclusivo...", "warning")
            with context:
                plugin_result = plugin.run(normalized_url)

            if not isinstance(plugin_result, dict):
                raise TypeError("Plugin retornou um valor inválido; esperado dict.")
            plugin_result["peso"] = float(getattr(plugin, "weight", plugin_result.get("peso", 1)))
            result["plugins"][name] = plugin_result

            status = plugin_result.get("status", "ok")
            score = float(plugin_result.get("score", 0) or 0)
            level = "success" if status == "ok" else "warning" if status == "not_applicable" else "error"
            _emit(progress, f"{name}: {status} | score {score:.2f}", level)
        except Exception as exc:
            weight = float(getattr(plugin, "weight", 1))
            result["plugins"][name] = {
                "status": "error",
                "score": 0,
                "peso": weight,
                "erro": str(exc),
                "detalhes": {},
            }
            _emit(progress, f"{name}: erro - {exc}", "error")

    config = ConfigLoader(str(BASE_DIR / "config" / "config.json"))
    threshold = float(config.get_global_config().get("minimum_coverage_for_ranking", 80))
    score_details = Scorer(threshold).calculate_analysis(result["plugins"])
    result.update(score_details)
    result["fim"] = datetime.now().isoformat()

    output_path.mkdir(parents=True, exist_ok=True)
    latest_file = output_path / "data.json"
    latest_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["arquivo_resultado"] = str(latest_file.relative_to(BASE_DIR))

    if save_history:
        history_dir = output_path / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = re.sub(r"[^a-zA-Z0-9_-]+", "_", urlparse(normalized_url).netloc).strip("_") or "site"
        history_file = history_dir / f"{stamp}_{domain}.json"
        result["arquivo_historico"] = str(history_file.relative_to(BASE_DIR))
        history_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        latest_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    level = "success" if result["rankable"] else "warning"
    _emit(
        progress,
        f"Score final: {result['score_final']:.2f} - {result['ranking']} | cobertura {result['coverage']:.1f}%",
        level,
    )
    return result
