"""
core/config_loader.py
Carregador de configurações do sistema
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega o arquivo de configuração"""
        if not self.config_file.exists():
            print(f"⚠️  Arquivo de configuração não encontrado: {self.config_file}")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Erro ao carregar configuração: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
        return {
            "ortografia": {
                "enabled": True,
                "language": "pt-BR",
                "max_errors": 50,
                "weight": 0.7
            },
            "links": {
                "enabled": True,
                "max_links_check": 100,
                "timeout": 5,
                "weight": 1.3
            },
            "imagens": {
                "enabled": True,
                "max_images_check": 50,
                "weight": 1.2
            },
            "social_media": {
                "enabled": True,
                "weight": 0.3
            },
            "lighthouse": {
                "enabled": True,
                "weight": 2.4
            },
            "seo": {
                "enabled": True,
                "weight": 1.5
            },
            "global": {
                "timeout": 30,
                "max_concurrent": 3,
                "retry_attempts": 2,
                "minimum_coverage_for_ranking": 80
            }
        }
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Retorna configuração de um plugin específico"""
        return self.config.get(plugin_name, {})
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Verifica se um plugin está habilitado"""
        plugin_config = self.get_plugin_config(plugin_name)
        return plugin_config.get('enabled', True)
    
    def get_plugin_weight(self, plugin_name: str) -> float:
        """Retorna o peso de um plugin"""
        plugin_config = self.get_plugin_config(plugin_name)
        return plugin_config.get('weight', 1.0)
    
    def get_global_config(self) -> Dict[str, Any]:
        """Retorna configurações globais"""
        return self.config.get('global', {})
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Salva configurações no arquivo"""
        try:
            data = config if config else self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
            return False
    
    def update_plugin_config(self, plugin_name: str, updates: Dict[str, Any]) -> bool:
        """Atualiza configuração de um plugin"""
        if plugin_name not in self.config:
            self.config[plugin_name] = {}
        
        self.config[plugin_name].update(updates)
        return self.save_config()