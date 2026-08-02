"""Plugin de ortografia leve e estável para ambientes como Railway.

Usa dicionário português em Python puro. Não abre um servidor Java por análise,
evita conflitos de portas e continua funcionando sem serviço externo.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable

from bs4 import BeautifulSoup
try:
    from spellchecker import SpellChecker
except ImportError:  # permite o app subir e reportar a dependência ausente
    SpellChecker = None

from core.http_client import get_html


class OrtografiaPlugin:
    def __init__(self):
        self.name = "ortografia"
        self.description = "Verifica possíveis erros ortográficos em português"
        self.weight = 0.7
        self.config: Dict[str, Any] = {}

    def run(self, url: str) -> Dict[str, Any]:
        try:
            if SpellChecker is None:
                raise RuntimeError("Dependência pyspellchecker não instalada. Rode: pip install -r requirements.txt")
            response = get_html(url, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            page_language = str((soup.html or {}).get("lang", "")).lower() if soup.html else ""

            if page_language and not page_language.startswith("pt"):
                return {
                    "status": "not_applicable",
                    "score": 100,
                    "peso": self.weight,
                    "erro": None,
                    "detalhes": {
                        "idioma_detectado": page_language,
                        "motivo": "Página declarada em outro idioma; o corretor pt-BR não foi aplicado.",
                    },
                }

            for tag in soup(["script", "style", "noscript", "svg", "code", "pre"]):
                tag.decompose()

            text = " ".join(soup.get_text(" ", strip=True).split())
            max_words = int(self.config.get("max_words", 1200))
            max_errors = int(self.config.get("max_errors", 30))
            words = list(self._candidate_words(text))[:max_words]

            if not words:
                return {
                    "status": "not_applicable",
                    "score": 100,
                    "peso": self.weight,
                    "erro": None,
                    "detalhes": {"total_palavras": 0, "motivo": "Não há texto suficiente para avaliar."},
                }

            spell = SpellChecker(language="pt", distance=1)
            ignore_words = {str(item).lower() for item in self.config.get("ignore_words", [])}
            spell.word_frequency.load_words(ignore_words)

            normalized = [word.lower() for word in words]
            counts = Counter(normalized)
            unknown = sorted(spell.unknown(counts.keys()), key=lambda item: (-counts[item], item))
            error_occurrences = sum(counts[word] for word in unknown)
            error_rate = error_occurrences / max(len(normalized), 1) * 100

            # O dicionário pode marcar nomes próprios e termos de marca. Por isso a
            # penalização é moderada e o plugin tem peso menor no score global.
            score = max(0.0, 100 - min(50.0, error_rate * 4.0))

            main_errors = []
            for word in unknown[:max_errors]:
                suggestion = spell.correction(word)
                candidates = sorted(spell.candidates(word) or [])[:3]
                main_errors.append({
                    "erro": word,
                    "ocorrencias": counts[word],
                    "sugestao": suggestion if suggestion and suggestion != word else None,
                    "alternativas": candidates,
                })

            return {
                "status": "ok",
                "score": round(score, 2),
                "peso": self.weight,
                "erro": None,
                "detalhes": {
                    "idioma_detectado": page_language or "pt presumido",
                    "motor": "pyspellchecker-pt",
                    "total_palavras": len(normalized),
                    "total_erros": error_occurrences,
                    "palavras_suspeitas_unicas": len(unknown),
                    "taxa_erro": round(error_rate, 2),
                    "erros_principais": main_errors[:10],
                    "observacao": "Nomes próprios, marcas e termos técnicos podem gerar falsos positivos.",
                },
            }
        except Exception as exc:
            return {"status": "error", "score": 0, "peso": self.weight, "erro": str(exc), "detalhes": {}}

    @staticmethod
    def _candidate_words(text: str) -> Iterable[str]:
        for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]{3,}", text):
            if token.isupper():
                continue
            if any(char.isdigit() for char in token):
                continue
            # Nomes próprios e marcas em CamelCase geram muito ruído.
            if token[0].isupper() and not token.isupper():
                continue
            yield token
