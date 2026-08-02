"""Plugin de imagens com amostragem leve e pontuação gradual."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from typing import Any, Dict
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError

from core.http_client import build_session, get_html


class ImagensPlugin:
    def __init__(self):
        self.name = "imagens"
        self.description = "Analisa acessibilidade, disponibilidade e peso das imagens"
        self.weight = 1.2
        self.config: Dict[str, Any] = {}

    def run(self, url: str) -> Dict[str, Any]:
        try:
            timeout = float(self.config.get("timeout", 8))
            max_images = int(self.config.get("max_images_check", 30))
            max_workers = max(1, min(int(self.config.get("max_workers", 4)), 6))
            max_download = int(self.config.get("max_download_bytes", 2_500_000))
            max_size_kb = int(self.config.get("max_size_kb", 700))

            response = get_html(url, timeout=max(timeout, 10))
            soup = BeautifulSoup(response.text, "html.parser")

            images = []
            seen = set()
            for tag in soup.find_all("img"):
                src = self._image_src(tag)
                if not src:
                    continue
                absolute = urljoin(response.url, src)
                parsed = urlparse(absolute)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc or absolute in seen:
                    continue
                seen.add(absolute)
                images.append({
                    "url": absolute,
                    "alt": tag.get("alt"),
                    "title": tag.get("title", ""),
                    "width_attr": tag.get("width"),
                    "height_attr": tag.get("height"),
                    "loading": tag.get("loading"),
                })

            if not images:
                return self._success(100.0, {
                    "total_imagens": 0,
                    "imagens_verificadas": 0,
                    "sem_alt": 0,
                    "sem_dimensoes": 0,
                    "muito_grandes": 0,
                    "faltando": 0,
                    "nao_aplicavel": True,
                    "problemas": {},
                })

            sample = images[:max_images]
            missing_alt = [img for img in images if img["alt"] is None]
            missing_dimensions = [img for img in images if not img["width_attr"] or not img["height_attr"]]
            broken = []
            oversized = []
            analyzed = []

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(self._inspect_image, img["url"], timeout, max_download, max_size_kb): img
                    for img in sample
                }
                for future in as_completed(future_map):
                    img = future_map[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = {"state": "indeterminate", "erro": str(exc)}
                    enriched = {**img, **result}
                    analyzed.append(enriched)
                    if result.get("state") == "broken":
                        broken.append(enriched)
                    elif result.get("oversized"):
                        oversized.append(enriched)

            total_markup = len(images)
            checked = max(len(sample), 1)
            missing_alt_rate = len(missing_alt) / total_markup
            missing_dimension_rate = len(missing_dimensions) / total_markup
            broken_rate = len(broken) / checked
            oversized_rate = len(oversized) / checked

            # Alt ausente, imagem indisponível e payload alto são problemas distintos.
            # A fórmula evita zeros artificiais por dupla contagem do mesmo arquivo.
            score = 100
            score -= missing_alt_rate * 35
            score -= broken_rate * 40
            score -= oversized_rate * 15
            score -= missing_dimension_rate * 10
            score = max(0.0, min(100.0, score))

            return self._success(score, {
                "total_imagens": total_markup,
                "imagens_verificadas": len(sample),
                "sem_alt": len(missing_alt),
                "sem_dimensoes": len(missing_dimensions),
                "muito_grandes": len(oversized),
                "faltando": len(broken),
                "taxa_sem_alt": round(missing_alt_rate * 100, 2),
                "taxa_faltando": round(broken_rate * 100, 2),
                "problemas": {
                    "sem_alt": missing_alt[:5],
                    "sem_dimensoes": missing_dimensions[:5],
                    "muito_grandes": oversized[:5],
                    "faltando": broken[:5],
                },
                "amostra": analyzed[:10],
            })
        except Exception as exc:
            return self._error(exc)

    @staticmethod
    def _image_src(tag) -> str | None:
        src = tag.get("src") or tag.get("data-src") or tag.get("data-lazy-src")
        if src:
            return str(src).strip()
        srcset = tag.get("srcset") or tag.get("data-srcset")
        if srcset:
            first = str(srcset).split(",", 1)[0].strip()
            return first.split(" ", 1)[0]
        return None

    def _inspect_image(self, url: str, timeout: float, max_download: int, max_size_kb: int) -> Dict[str, Any]:
        session = build_session()
        try:
            response = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
            status = response.status_code
            if status >= 400:
                return {"state": "broken", "status": status, "erro": f"HTTP {status}"}

            content_length = int(response.headers.get("content-length") or 0)
            if content_length > max_download:
                return {
                    "state": "ok",
                    "status": status,
                    "tamanho": content_length,
                    "oversized": content_length > max_size_kb * 1024,
                    "formato": response.headers.get("content-type", ""),
                    "leitura_limitada": True,
                }

            chunks = []
            total = 0
            for chunk in response.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                chunks.append(chunk)
                total += len(chunk)
                if total > max_download:
                    break

            payload = b"".join(chunks)
            result: Dict[str, Any] = {
                "state": "ok",
                "status": status,
                "tamanho": total,
                "oversized": total > max_size_kb * 1024,
                "content_type": response.headers.get("content-type", ""),
            }
            if total <= max_download:
                try:
                    image = Image.open(BytesIO(payload))
                    result.update({
                        "largura": image.size[0],
                        "altura": image.size[1],
                        "formato": image.format,
                    })
                except (UnidentifiedImageError, OSError):
                    # SVG, AVIF e formatos servidos dinamicamente podem não abrir no Pillow.
                    result["formato"] = response.headers.get("content-type", "desconhecido")
            return result
        except Exception as exc:
            return {"state": "indeterminate", "status": None, "erro": str(exc), "oversized": False}
        finally:
            session.close()

    def _success(self, score: float, details: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "score": round(score, 2), "peso": self.weight, "erro": None, "detalhes": details}

    def _error(self, exc: Exception) -> Dict[str, Any]:
        return {"status": "error", "score": 0, "peso": self.weight, "erro": str(exc), "detalhes": {}}
