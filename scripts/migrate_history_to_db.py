"""Importa o histórico JSON local para o banco configurado em DATABASE_URL.

Uso:
    python scripts/migrate_history_to_db.py
    python scripts/migrate_history_to_db.py --include-latest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.storage import ResultStorage  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Migra JSONs do Colheiteira para Supabase/Postgres.")
    parser.add_argument("--include-latest", action="store_true", help="também importa output/data.json")
    args = parser.parse_args()

    output_dir = BASE_DIR / "output"
    storage = ResultStorage(BASE_DIR, output_dir)
    if storage.name != "database":
        print("ERRO: banco não ativo. Defina DATABASE_URL e use STORAGE_BACKEND=database ou auto.")
        health = storage.health()
        if health.get("initialization_error"):
            print(health["initialization_error"])
        return 2

    paths = sorted((output_dir / "history").glob("*.json"))
    if args.include_latest and (output_dir / "data.json").exists():
        paths.append(output_dir / "data.json")

    imported = 0
    failed = 0
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            filename = path.name if path.name != "data.json" else None
            saved = storage.save(data, filename=filename)
            print(f"OK  {path.name} -> {saved.get('storage_id')}")
            imported += 1
        except Exception as exc:
            print(f"ERRO {path.name}: {exc}")
            failed += 1

    print(f"\nImportados: {imported} | Falhas: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
