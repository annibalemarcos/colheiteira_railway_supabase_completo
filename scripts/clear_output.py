"""Limpa resultado antigo do dashboard Colheiteira.

Use quando o painel estiver mostrando uma análise velha de `output/data.json`.
Por padrão apaga só a última análise; passe --history para apagar também o histórico.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"
HISTORY = OUTPUT / "history"


def remove(path: Path) -> bool:
    if path.exists() and path.is_file():
        path.unlink()
        print("[OK] Removido:", path.relative_to(ROOT))
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Limpa resultados antigos do dashboard.")
    parser.add_argument("--history", action="store_true", help="também apaga output/history/*.json")
    args = parser.parse_args()

    removed = 0
    removed += int(remove(OUTPUT / "data.json"))

    if args.history and HISTORY.exists():
        for path in HISTORY.glob("*.json"):
            removed += int(remove(path))

    if not removed:
        print("[OK] Nada antigo para apagar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
