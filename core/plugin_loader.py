"""
core/plugin_loader.py
Carregador dinâmico de plugins
"""
import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, Any

class PluginLoader:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins = {}
    
    def load_all_plugins(self) -> Dict[str, Any]:
        """Carrega todos os plugins disponíveis"""
        if not self.plugins_dir.exists():
            print(f"❌ Diretório de plugins não encontrado: {self.plugins_dir}")
            return {}
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                plugin_file = plugin_dir / "plugin.py"
                
                if plugin_file.exists():
                    try:
                        plugin = self._load_plugin(plugin_dir.name, plugin_file)
                        if plugin:
                            self.plugins[plugin_dir.name] = plugin
                    except Exception as e:
                        print(f"⚠️  Erro ao carregar plugin {plugin_dir.name}: {e}")
        
        return self.plugins
    
    def _load_plugin(self, name: str, plugin_file: Path) -> Any:
        """Carrega um plugin específico"""
        spec = importlib.util.spec_from_file_location(name, plugin_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            
            # Procura pela classe do plugin
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.lower().endswith('plugin') and 
                    attr_name != 'Plugin'):
                    return attr()
        
        return None
    
    def get_plugin(self, name: str) -> Any:
        """Retorna um plugin específico"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> list:
        """Lista todos os plugins carregados"""
        return list(self.plugins.keys())