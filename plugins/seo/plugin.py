"""Plugin SEO on-page calibrado para páginas reais e respostas do Railway."""
from __future__ import annotations

from typing import Any, Dict
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from core.http_client import build_session, get_html


class SeoPlugin:
    def __init__(self):
        self.name = "seo"
        self.description = "Análise de SEO on-page e elementos técnicos básicos"
        self.weight = 1.5
        self.config: Dict[str, Any] = {}

    def run(self, url: str) -> Dict[str, Any]:
        try:
            response = get_html(url, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            problems = []
            score = 100.0

            title = soup.find("title")
            title_text = title.get_text(" ", strip=True) if title else ""
            if not title_text:
                score -= 18
                problems.append(self._problem("critical", "Title", "Tag <title> não encontrada", "Alto"))
            elif len(title_text) < 15 or len(title_text) > 70:
                score -= 4
                problems.append(self._problem("warning", "Title", f"Comprimento fora da faixa prática ({len(title_text)} caracteres)", "Médio"))

            meta_desc = soup.find("meta", attrs={"name": lambda value: value and value.lower() == "description"})
            description = str(meta_desc.get("content", "")).strip() if meta_desc else ""
            if not description:
                score -= 10
                problems.append(self._problem("warning", "Meta description", "Meta description não encontrada", "Médio"))
            elif len(description) < 70 or len(description) > 180:
                score -= 3
                problems.append(self._problem("info", "Meta description", f"Comprimento fora da faixa prática ({len(description)} caracteres)", "Baixo"))

            h1_tags = soup.find_all("h1")
            if not h1_tags:
                score -= 8
                problems.append(self._problem("warning", "H1", "Nenhuma tag H1 encontrada", "Médio"))
            elif len(h1_tags) > 3:
                score -= 3
                problems.append(self._problem("info", "H1", f"Foram encontradas {len(h1_tags)} tags H1", "Baixo"))

            canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
            canonical = str(canonical_tag.get("href", "")).strip() if canonical_tag else ""
            if not canonical:
                score -= 4
                problems.append(self._problem("info", "Canonical", "URL canônica não encontrada", "Baixo"))

            viewport = soup.find("meta", attrs={"name": lambda value: value and value.lower() == "viewport"})
            if not viewport:
                score -= 8
                problems.append(self._problem("warning", "Viewport", "Meta viewport não encontrada", "Médio"))

            html_lang = str((soup.html or {}).get("lang", "")).strip() if soup.html else ""
            if not html_lang:
                score -= 4
                problems.append(self._problem("info", "Idioma", "Atributo lang não encontrado no HTML", "Baixo"))

            images = soup.find_all("img")
            images_without_alt = [img for img in images if img.get("alt") is None]
            if images:
                missing_alt_rate = len(images_without_alt) / len(images)
                alt_penalty = min(8.0, missing_alt_rate * 8.0)
                score -= alt_penalty
                if images_without_alt:
                    problems.append(self._problem("warning", "Imagens", f"{len(images_without_alt)} de {len(images)} imagens sem atributo alt", "Médio"))
            else:
                missing_alt_rate = 0.0

            links = soup.find_all("a", href=True)
            origin = urlsplit(response.url)
            internal_links = 0
            external_links = 0
            for link in links:
                absolute = urljoin(response.url, str(link.get("href", "")))
                parsed = urlsplit(absolute)
                if parsed.scheme not in {"http", "https"}:
                    continue
                if parsed.netloc == origin.netloc:
                    internal_links += 1
                else:
                    external_links += 1

            base_url = f"{origin.scheme}://{origin.netloc}"
            sitemap = self._resource_exists(urljoin(base_url, "/sitemap.xml")) or self._resource_exists(urljoin(base_url, "/sitemap_index.xml"))
            robots = self._resource_exists(urljoin(base_url, "/robots.txt"))
            if not sitemap:
                score -= 3
                problems.append(self._problem("info", "Sitemap", "Sitemap XML não confirmado", "Baixo"))
            if not robots:
                score -= 2
                problems.append(self._problem("info", "Robots.txt", "Robots.txt não confirmado", "Baixo"))

            structured_data = bool(soup.find("script", attrs={"type": "application/ld+json"}))
            score = max(0.0, min(100.0, score))

            return {
                "status": "ok",
                "score": round(score, 2),
                "peso": self.weight,
                "erro": None,
                "detalhes": {
                    "total_problemas": len(problems),
                    "problemas_criticos": sum(1 for item in problems if item["tipo"] == "critical"),
                    "problemas_warnings": sum(1 for item in problems if item["tipo"] == "warning"),
                    "problemas": problems[:12],
                    "metricas": {
                        "status_http": response.status_code,
                        "url_final": response.url,
                        "title_length": len(title_text),
                        "meta_desc_length": len(description),
                        "h1_count": len(h1_tags),
                        "images_total": len(images),
                        "images_sem_alt": len(images_without_alt),
                        "taxa_imagens_sem_alt": round(missing_alt_rate * 100, 2),
                        "links_internos": internal_links,
                        "links_externos": external_links,
                        "tem_canonical": bool(canonical),
                        "tem_viewport": bool(viewport),
                        "tem_lang": bool(html_lang),
                        "tem_sitemap": sitemap,
                        "tem_robots": robots,
                        "tem_dados_estruturados": structured_data,
                    },
                },
            }
        except Exception as exc:
            return {"status": "error", "score": 0, "peso": self.weight, "erro": str(exc), "detalhes": {}}

    @staticmethod
    def _problem(kind: str, element: str, problem: str, impact: str) -> Dict[str, str]:
        return {"tipo": kind, "elemento": element, "problema": problem, "impacto": impact}

    @staticmethod
    def _resource_exists(url: str) -> bool:
        session = build_session()
        try:
            response = session.head(url, timeout=6, allow_redirects=True)
            if response.status_code in {405, 501}:
                response = session.get(url, timeout=6, allow_redirects=True, stream=True)
            return 200 <= response.status_code < 400
        except Exception:
            return False
        finally:
            session.close()
