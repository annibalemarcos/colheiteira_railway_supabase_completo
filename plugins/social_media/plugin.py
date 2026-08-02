"""Plugin de presença social baseado apenas no HTML da página.

Não abre perfis externos: isso evita bloqueios, CAPTCHA e resultados simulados.
"""
from __future__ import annotations

import re
from typing import Any, Dict

from bs4 import BeautifulSoup

from core.http_client import get_html


class SocialMediaPlugin:
    def __init__(self):
        self.name = "social_media"
        self.description = "Analisa metadados sociais e links oficiais"
        self.weight = 0.3
        self.config: Dict[str, Any] = {}
        self.social_patterns = {
            "facebook": r"(?:www\.)?facebook\.com/",
            "instagram": r"(?:www\.)?instagram\.com/",
            "x_twitter": r"(?:www\.)?(?:x|twitter)\.com/",
            "linkedin": r"(?:www\.)?linkedin\.com/",
            "youtube": r"(?:www\.)?(?:youtube\.com|youtu\.be)/",
            "tiktok": r"(?:www\.)?tiktok\.com/",
        }

    def run(self, url: str) -> Dict[str, Any]:
        try:
            response = get_html(url, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")

            links: Dict[str, str] = {}
            for tag in soup.find_all("a", href=True):
                href = str(tag.get("href", ""))
                for network, pattern in self.social_patterns.items():
                    if network not in links and re.search(pattern, href, flags=re.I):
                        links[network] = href

            metadata = {
                "og_title": self._meta(soup, property="og:title"),
                "og_description": self._meta(soup, property="og:description"),
                "og_image": self._meta(soup, property="og:image"),
                "og_url": self._meta(soup, property="og:url"),
                "twitter_card": self._meta(soup, name="twitter:card"),
                "canonical": self._canonical(soup),
            }

            score = 0.0
            score += 15 if metadata["og_title"] else 0
            score += 15 if metadata["og_description"] else 0
            score += 20 if metadata["og_image"] else 0
            score += 10 if metadata["og_url"] else 0
            score += 10 if metadata["twitter_card"] else 0
            score += 10 if metadata["canonical"] else 0
            score += min(20, len(links) * 5)

            return {
                "status": "ok",
                "score": round(min(100.0, score), 2),
                "peso": self.weight,
                "erro": None,
                "detalhes": {
                    "redes_encontradas": len(links),
                    "redes": links,
                    "metadados": {key: bool(value) for key, value in metadata.items()},
                    "observacao": "A nota mede prontidão de compartilhamento e presença de links; não mede frequência de posts nem engajamento.",
                },
            }
        except Exception as exc:
            return {"status": "error", "score": 0, "peso": self.weight, "erro": str(exc), "detalhes": {}}

    @staticmethod
    def _meta(soup: BeautifulSoup, **attrs: str) -> str | None:
        tag = soup.find("meta", attrs=attrs)
        return str(tag.get("content", "")).strip() if tag and tag.get("content") else None

    @staticmethod
    def _canonical(soup: BeautifulSoup) -> str | None:
        tag = soup.find("link", rel=lambda value: value and "canonical" in value)
        return str(tag.get("href", "")).strip() if tag and tag.get("href") else None
