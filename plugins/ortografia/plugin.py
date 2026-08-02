"""
plugins/ortografia/plugin.py
Plugin para análise de erros ortográficos
"""
import re
from typing import Dict, Any
import language_tool_python
from bs4 import BeautifulSoup
import requests

class OrtografiaPlugin:
    def __init__(self):
        self.name = "ortografia"
        self.description = "Analisa erros ortográficos no conteúdo"
        self.weight = 1.5
        self.tool = language_tool_python.LanguageTool('pt-BR')
    
    def run(self, url: str) -> Dict[str, Any]:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts e styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            text = ' '.join(text.split())
            
            # Análise ortográfica
            matches = self.tool.check(text)
            
            erros = []
            for match in matches[:50]:  # Limita a 50 erros
                matched_text = self._match_value(match, "matchedText", "matched_text")
                if not matched_text:
                    offset = self._match_value(match, "offset", default=0) or 0
                    length = self._match_value(match, "errorLength", "error_length", default=0) or 0
                    try:
                        matched_text = text[int(offset):int(offset) + int(length)]
                    except Exception:
                        matched_text = ""

                erros.append({
                    "texto": self._match_value(match, "context", default=""),
                    "erro": matched_text,
                    "sugestao": (self._match_value(match, "replacements", default=[]) or [])[:3],
                    "tipo": self._match_value(match, "ruleId", "rule_id", default=""),
                    "mensagem": self._match_value(match, "message", default="")
                })
            
            # Cálculo do score
            total_palavras = len(text.split())
            taxa_erro = len(matches) / max(total_palavras, 1) * 100
            
            score = max(0, 100 - (taxa_erro * 10))
            
            # Benchmarks de concorrentes
            concorrentes = self._get_competitors_examples()
            
            return {
                "status": "ok",
                "score": round(score, 2),
                "peso": self.weight,
                "erro": None,
                "detalhes": {
                    "total_erros": len(matches),
                    "total_palavras": total_palavras,
                    "taxa_erro": round(taxa_erro, 2),
                    "erros_principais": erros[:10],
                    "concorrentes": concorrentes
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "score": 0,
                "peso": self.weight,
                "erro": str(e),
                "detalhes": {}
            }
    
    def _match_value(self, match, *names, default=None):
        """Compatibilidade entre versões do language-tool-python.

        Algumas versões usam camelCase (matchedText/ruleId), outras usam
        snake_case (matched_text/rule_id). Sem isso o plugin caía com:
        "Match object has no attribute 'matchedText'".
        """
        for name in names:
            if hasattr(match, name):
                return getattr(match, name)
        return default

    def _get_competitors_examples(self):
        """Retorna exemplos de concorrentes com boa ortografia"""
        return [
            {
                "nome": "Amazon Brasil",
                "url": "https://amazon.com.br",
                "taxa_erro": 0.02,
                "motivo": "Usa revisão profissional e ferramentas automatizadas"
            },
            {
                "nome": "Nubank",
                "url": "https://nubank.com.br",
                "taxa_erro": 0.01,
                "motivo": "Time dedicado de content writers e revisores"
            },
            {
                "nome": "Magazin Luiza",
                "url": "https://magazineluiza.com.br",
                "taxa_erro": 0.03,
                "motivo": "Processo rigoroso de QA textual"
            }
        ]