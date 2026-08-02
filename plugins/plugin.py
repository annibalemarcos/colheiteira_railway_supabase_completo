"""
plugins/plugin.py
Classe base para todos os plugins
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class Plugin(ABC):
    """Classe base abstrata para plugins de análise"""
    
    def __init__(self):
        self.name = "base_plugin"
        self.description = "Plugin base"
        self.weight = 1.0
        self.version = "1.0.0"
    
    @abstractmethod
    def run(self, url: str) -> Dict[str, Any]:
        """
        Executa a análise do plugin
        
        Args:
            url: URL do site a ser analisado
        
        Returns:
            Dict com estrutura:
            {
                "status": "ok" | "error",
                "score": float (0-100),
                "peso": float,
                "erro": str | None,
                "detalhes": dict
            }
        """
        pass
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Valida se o resultado está no formato correto"""
        required_keys = ['status', 'score', 'peso', 'erro', 'detalhes']
        return all(key in result for key in required_keys)
    
    def create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Cria um resultado de erro padronizado"""
        return {
            "status": "error",
            "score": 0,
            "peso": self.weight,
            "erro": error_message,
            "detalhes": {}
        }
    
    def create_success_result(self, score: float, detalhes: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um resultado de sucesso padronizado"""
        return {
            "status": "ok",
            "score": round(score, 2),
            "peso": self.weight,
            "erro": None,
            "detalhes": detalhes
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o plugin"""
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "version": self.version
        }