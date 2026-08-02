"""
core/plugin_loader.py
Carregador dinâmico de plugins.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict


class PluginLoader:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, Any] = {}
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        config_file = self.plugins_dir.resolve().parent / "config" / "config.json"
        try:
            return json.loads(config_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def load_all_plugins(self) -> Dict[str, Any]:
        """Carrega plugins ativos em ordem estável."""
        if not self.plugins_dir.exists():
            print(f"❌ Diretório de plugins não encontrado: {self.plugins_dir}")
            return {}

        preferred_order = {
            "seo": 10,
            "links": 20,
            "imagens": 30,
            "social_media": 40,
            "ortografia": 50,
            "lighthouse": 60,
        }
        plugin_dirs = sorted(
            (p for p in self.plugins_dir.iterdir() if p.is_dir() and not p.name.startswith("_")),
            key=lambda p: (preferred_order.get(p.name, 999), p.name),
        )

        for plugin_dir in plugin_dirs:
            plugin_file = plugin_dir / "plugin.py"
            if not plugin_file.exists():
                continue

            plugin_config = self.config.get(plugin_dir.name, {})
            if plugin_config.get("enabled", True) is False:
                continue

            try:
                plugin = self._load_plugin(plugin_dir.name, plugin_file)
                if plugin:
                    plugin.config = plugin_config
                    plugin.weight = float(plugin_config.get("weight", getattr(plugin, "weight", 1.0)))
                    self.plugins[plugin_dir.name] = plugin
            except Exception as exc:
                print(f"⚠️  Erro ao carregar plugin {plugin_dir.name}: {exc}")

        return self.plugins

    def _load_plugin(self, name: str, plugin_file: Path) -> Any:
        """Carrega um plugin específico."""
        module_name = f"colheiteira_plugin_{name}"
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and attr_name.lower().endswith("plugin")
                    and attr_name != "Plugin"
                ):
                    return attr()
        return None

    def get_plugin(self, name: str) -> Any:
        return self.plugins.get(name)

    def list_plugins(self) -> list:
        return list(self.plugins.keys())
