from __future__ import annotations

from plugins.imagens import plugin as images_module
from plugins.links import plugin as links_module
from plugins.seo import plugin as seo_module
from plugins.social_media import plugin as social_module


class FakeResponse:
    def __init__(self, html: str, url: str = "https://example.test/", status_code: int = 200):
        self.text = html
        self.url = url
        self.status_code = status_code


def test_links_with_no_links_is_not_punished(monkeypatch):
    monkeypatch.setattr(links_module, "get_html", lambda *args, **kwargs: FakeResponse("<html><body><h1>Olá</h1></body></html>"))
    plugin = links_module.LinksPlugin()
    plugin.config = {}

    result = plugin.run("https://example.test/")

    assert result["status"] == "ok"
    assert result["score"] == 100
    assert result["detalhes"]["nao_aplicavel"] is True


def test_page_without_images_is_not_punished(monkeypatch):
    monkeypatch.setattr(images_module, "get_html", lambda *args, **kwargs: FakeResponse("<html><body><h1>Olá</h1></body></html>"))
    plugin = images_module.ImagensPlugin()
    plugin.config = {}

    result = plugin.run("https://example.test/")

    assert result["status"] == "ok"
    assert result["score"] == 100
    assert result["detalhes"]["nao_aplicavel"] is True


def test_social_score_uses_page_metadata_without_opening_profiles(monkeypatch):
    html = """
    <html><head>
      <meta property="og:title" content="Título">
      <meta property="og:description" content="Descrição">
      <meta property="og:image" content="https://example.test/image.jpg">
      <meta property="og:url" content="https://example.test/">
      <meta name="twitter:card" content="summary_large_image">
      <link rel="canonical" href="https://example.test/">
    </head><body><a href="https://instagram.com/example">Instagram</a></body></html>
    """
    monkeypatch.setattr(social_module, "get_html", lambda *args, **kwargs: FakeResponse(html))
    plugin = social_module.SocialMediaPlugin()

    result = plugin.run("https://example.test/")

    assert result["status"] == "ok"
    assert result["score"] == 85
    assert result["detalhes"]["redes_encontradas"] == 1


def test_seo_uses_gradual_penalties(monkeypatch):
    html = """
    <html lang="pt-BR"><head>
      <title>Página de teste suficientemente clara</title>
      <meta name="description" content="Uma descrição útil e suficientemente completa para representar esta página de teste de maneira objetiva.">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="canonical" href="https://example.test/">
    </head><body><h1>Título principal</h1></body></html>
    """
    monkeypatch.setattr(seo_module, "get_html", lambda *args, **kwargs: FakeResponse(html))
    monkeypatch.setattr(seo_module.SeoPlugin, "_resource_exists", staticmethod(lambda url: True))
    plugin = seo_module.SeoPlugin()

    result = plugin.run("https://example.test/")

    assert result["status"] == "ok"
    assert result["score"] >= 95
