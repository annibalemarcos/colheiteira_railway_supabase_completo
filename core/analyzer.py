"""
core/analyzer.py
Motor reaproveitável da análise web.

A CLI (`main.py`) e o dashboard Flask usam esta função para evitar código duplicado.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

from core.plugin_loader import PluginLoader
from core.scorer import Scorer

ProgressCallback = Optional[Callable[[str, str], None]]

BASE_DIR = Path(__file__).resolve().parent.parent


def normalize_url(url: str) -> str:
    """Normaliza uma URL digitada pelo usuário."""
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
    """Executa a análise completa e salva o resultado em JSON.

    Args:
        url: URL alvo.
        progress: callback opcional no formato `(mensagem, nivel)`.
        output_dir: pasta onde `data.json` e `history/` serão salvos.
        save_history: se True, cria uma cópia versionada no histórico.
    """
    normalized_url = normalize_url(url)
    output_path = Path(output_dir) if output_dir else BASE_DIR / "output"
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path

    _emit(progress, f"Iniciando análise completa de {normalized_url}", "info")

    loader = PluginLoader(str(BASE_DIR / "plugins"))
    plugins = loader.load_all_plugins()
    _emit(progress, f"{len(plugins)} plugin(s) carregado(s).", "success")

    resultado: Dict[str, Any] = {
        "url": normalized_url,
        "inicio": datetime.now().isoformat(),
        "plugins": {},
    }

    for nome, plugin in plugins.items():
        _emit(progress, f"Executando plugin: {nome}", "info")
        try:
            resultado_plugin = plugin.run(normalized_url)
            if not isinstance(resultado_plugin, dict):
                raise TypeError("Plugin retornou um valor inválido; esperado dict.")

            resultado["plugins"][nome] = resultado_plugin
            status = resultado_plugin.get("status", "ok")
            score = float(resultado_plugin.get("score", 0) or 0)
            level = "success" if status == "ok" else "error"
            _emit(progress, f"{nome}: {status} | score {score:.2f}", level)
        except Exception as exc:  # mantém os outros plugins vivos
            peso = getattr(plugin, "weight", 1)
            resultado["plugins"][nome] = {
                "status": "error",
                "score": 0,
                "peso": peso,
                "erro": str(exc),
                "detalhes": {},
            }
            _emit(progress, f"{nome}: erro - {exc}", "error")

    scorer = Scorer()
    score_final = scorer.calculate_final_score(resultado["plugins"])
    ranking = scorer.get_ranking(score_final)

    resultado["score_final"] = score_final
    resultado["ranking"] = ranking
    resultado["fim"] = datetime.now().isoformat()

    output_path.mkdir(parents=True, exist_ok=True)
    latest_file = output_path / "data.json"
    latest_file.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    resultado["arquivo_resultado"] = str(latest_file.relative_to(BASE_DIR))

    if save_history:
        history_dir = output_path / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = re.sub(r"[^a-zA-Z0-9_-]+", "_", urlparse(normalized_url).netloc).strip("_") or "site"
        history_file = history_dir / f"{stamp}_{domain}.json"
        resultado["arquivo_historico"] = str(history_file.relative_to(BASE_DIR))
        history_file.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        # Regrava latest já com o caminho do histórico preenchido.
        latest_file.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    _emit(progress, f"Score final: {score_final:.2f} - {ranking}", "success")
    return resultado
