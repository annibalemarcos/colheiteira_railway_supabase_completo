"""
main.py
Sistema completo de análise web do Colheiteira.

Uso:
    python main.py https://seusite.com

Depois abra o dashboard:
    python server/app.py
    http://localhost:5840
"""
from __future__ import annotations

import sys
from pathlib import Path

from core.analyzer import run_analysis
from core.storage import ResultStorage


def _progress(message: str, level: str = "info") -> None:
    icons = {
        "info": "🔍",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
    }
    print(f"{icons.get(level, '•')} {message}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python main.py <URL>")
        print("Exemplo: python main.py https://example.com")
        sys.exit(1)

    url = sys.argv[1]
    print(f"\n🚀 Colheiteira iniciada\n")

    try:
        resultado = run_analysis(url, progress=_progress)
        base_dir = Path(__file__).resolve().parent
        resultado = ResultStorage(base_dir, base_dir / "output").save(resultado)
    except Exception as exc:
        print(f"\n❌ Erro fatal: {exc}\n")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"📊 SCORE FINAL: {resultado['score_final']:.2f} - {resultado['ranking']}")
    print(f"{'=' * 60}")
    print(f"\n💾 Resultado salvo em: {resultado.get('arquivo_resultado', 'output/data.json')}")
    if resultado.get("arquivo_historico"):
        print(f"🗂️  Histórico salvo em: {resultado['arquivo_historico']}")
    print("🌐 Dashboard: python server/app.py")
    print("   Acesse: http://localhost:5840\n")


if __name__ == "__main__":
    main()
