"""Plugin de links com pontuação gradual e tolerância a bloqueios externos."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from core.http_client import build_session, get_html


class LinksPlugin:
    def __init__(self):
        self.name = "links"
        self.description = "Verifica links quebrados, lentos e indeterminados"
        self.weight = 1.3
        self.config: Dict[str, Any] = {}

    def run(self, url: str) -> Dict[str, Any]:
        try:
            timeout = float(self.config.get("timeout", 8))
            max_links = int(self.config.get("max_links_check", 60))
            max_workers = max(1, min(int(self.config.get("max_workers", 5)), 8))
            slow_threshold = float(self.config.get("slow_threshold_seconds", 3.5))

            response = get_html(url, timeout=max(timeout, 10))
            soup = BeautifulSoup(response.text, "html.parser")

            links = []
            seen = set()
            for tag in soup.find_all(["a", "link", "script", "img"]):
                raw = tag.get("href") or tag.get("src")
                if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                    continue
                absolute = urljoin(response.url, raw)
                parsed = urlparse(absolute)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    continue
                normalized = absolute.split("#", 1)[0]
                if normalized in seen:
                    continue
                seen.add(normalized)
                links.append({
                    "url": normalized,
                    "tipo": tag.name,
                    "texto": tag.get_text(" ", strip=True)[:80] if tag.name == "a" else (tag.get("alt") or "")[:80],
                })

            sample = links[:max_links]
            if not sample:
                return self._success(
                    100.0,
                    {
                        "total_links": 0,
                        "links_verificados": 0,
                        "links_quebrados": 0,
                        "links_lentos": 0,
                        "links_indeterminados": 0,
                        "taxa_quebrados": 0.0,
                        "nao_aplicavel": True,
                        "problemas": [],
                        "lentos": [],
                        "indeterminados": [],
                    },
                )

            broken = []
            slow = []
            indeterminate = []

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(self._check_link, item["url"], timeout, slow_threshold): item
                    for item in sample
                }
                for future in as_completed(future_map):
                    item = future_map[future]
                    try:
                        check = future.result()
                    except Exception as exc:
                        check = {"state": "indeterminate", "error": str(exc), "elapsed": 0.0}

                    enriched = {**item, **check}
                    if check["state"] == "broken":
                        broken.append(enriched)
                    elif check["state"] == "slow":
                        slow.append(enriched)
                    elif check["state"] == "indeterminate":
                        indeterminate.append(enriched)

            checked = len(sample)
            broken_rate = len(broken) / checked
            slow_rate = len(slow) / checked
            indeterminate_rate = len(indeterminate) / checked

            # Quebrados pesam bastante; lentidão e bloqueios/429 pesam pouco.
            score = 100 - (broken_rate * 80) - (slow_rate * 15) - (indeterminate_rate * 8)
            score = max(0.0, min(100.0, score))

            return self._success(
                score,
                {
                    "total_links": len(links),
                    "links_verificados": checked,
                    "links_quebrados": len(broken),
                    "links_lentos": len(slow),
                    "links_indeterminados": len(indeterminate),
                    "taxa_quebrados": round(broken_rate * 100, 2),
                    "taxa_lentos": round(slow_rate * 100, 2),
                    "taxa_indeterminados": round(indeterminate_rate * 100, 2),
                    "problemas": broken[:10],
                    "lentos": slow[:5],
                    "indeterminados": indeterminate[:5],
                },
            )
        except Exception as exc:
            return self._error(exc)

    def _check_link(self, url: str, timeout: float, slow_threshold: float) -> Dict[str, Any]:
        start = time.monotonic()
        session = build_session()
        try:
            response = session.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code in {405, 501}:
                response = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
            elapsed = time.monotonic() - start
            status = response.status_code

            if status in {401, 403, 429}:
                return {"state": "indeterminate", "status": status, "elapsed": round(elapsed, 3), "motivo": "acesso limitado"}
            if status == 404 or status == 410 or status >= 500:
                return {"state": "broken", "status": status, "elapsed": round(elapsed, 3)}
            if status >= 400:
                return {"state": "broken", "status": status, "elapsed": round(elapsed, 3)}
            if elapsed > slow_threshold:
                return {"state": "slow", "status": status, "elapsed": round(elapsed, 3)}
            return {"state": "ok", "status": status, "elapsed": round(elapsed, 3)}
        except Exception as exc:
            elapsed = time.monotonic() - start
            return {"state": "indeterminate", "status": None, "elapsed": round(elapsed, 3), "error": str(exc)}
        finally:
            session.close()

    def _success(self, score: float, details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "ok",
            "score": round(score, 2),
            "peso": self.weight,
            "erro": None,
            "detalhes": details,
        }

    def _error(self, exc: Exception) -> Dict[str, Any]:
        return {
            "status": "error",
            "score": 0,
            "peso": self.weight,
            "erro": str(exc),
            "detalhes": {},
        }
