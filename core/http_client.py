"""Cliente HTTP compartilhado pelos plugins.

Mantém cabeçalhos coerentes, limites previsíveis e evita que cada plugin faça
requisições com o User-Agent padrão do requests, frequentemente bloqueado.
"""
from __future__ import annotations

from typing import Optional

import requests

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "Colheiteira/2.0"
)


def build_session(user_agent: Optional[str] = None) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    return session


def get_html(url: str, *, timeout: float = 15.0) -> requests.Response:
    session = build_session()
    response = session.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    return response
