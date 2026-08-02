"""Diagnóstico rápido do Lighthouse usado pelo Colheiteira.

Este script NÃO importa `plugins.lighthouse.plugin` pelo pacote Python tradicional,
porque isso pode acionar `plugins/__init__.py` em instalações antigas.
Ele carrega o arquivo do plugin diretamente. Menos firula, menos drama.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_FILE = ROOT / "plugins" / "lighthouse" / "plugin.py"


def load_lighthouse_plugin_class():
    if not PLUGIN_FILE.exists():
        raise FileNotFoundError(f"Plugin Lighthouse não encontrado em: {PLUGIN_FILE}")

    spec = importlib.util.spec_from_file_location("colheiteira_lighthouse_plugin", PLUGIN_FILE)
    if not spec or not spec.loader:
        raise RuntimeError("Não foi possível montar o import direto do plugin Lighthouse.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.LighthousePlugin


def main() -> int:
    print("=" * 68)
    print("Diagnóstico Lighthouse")
    print("=" * 68)

    try:
        LighthousePlugin = load_lighthouse_plugin_class()
        plugin = LighthousePlugin()
        env = plugin._build_env()
        cmd = plugin._resolve_lighthouse_command(env)
    except Exception as exc:
        print("[ERRO] Falha ao carregar/testar o plugin Lighthouse:", exc)
        return 1

    if not cmd:
        print("[ERRO] Lighthouse não foi encontrado pelo Python.")
        print("\nTentativas que o app fez:")
        for candidate in plugin._candidate_commands(env, include_npx=True):
            print(" -", " ".join(candidate))
        print("\nComandos úteis no Windows:")
        print("  npm prefix -g")
        print("  where lighthouse")
        print("  where lighthouse.cmd")
        print("  npx --yes lighthouse --version")
        print("\nDica: feche e abra o terminal depois do `npm install -g lighthouse`.")
        return 1

    print("[OK] Comando encontrado:", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd + ["--version"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        version = (result.stdout or result.stderr).strip()
        print("Versão:", version or "não informada")
        if result.returncode == 0:
            print("[OK] Lighthouse pronto para uso no dashboard.")
        else:
            print("[ERRO] O comando foi encontrado, mas retornou erro.")
        return result.returncode
    except Exception as exc:
        print("[ERRO] Falha ao executar Lighthouse:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
