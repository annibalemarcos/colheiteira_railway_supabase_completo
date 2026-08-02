"""
plugins/seo/plugin.py
Plugin completo de análise SEO
"""
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

class SeoPlugin:
    def __init__(self):
        self.name = "seo"
        self.description = "Análise completa de SEO on-page"
        self.weight = 1.0
    
    def run(self, url: str) -> Dict[str, Any]:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            problemas = []
            score = 100
            
            # 1. Title Tag
            title = soup.find('title')
            if not title:
                problemas.append({
                    "tipo": "critical",
                    "elemento": "Title Tag",
                    "problema": "Tag <title> não encontrada",
                    "impacto": "Alto - Essencial para SEO"
                })
                score -= 15
            elif len(title.text) < 30:
                problemas.append({
                    "tipo": "warning",
                    "elemento": "Title Tag",
                    "problema": f"Title muito curto ({len(title.text)} caracteres)",
                    "impacto": "Médio - Ideal: 50-60 caracteres"
                })
                score -= 5
            elif len(title.text) > 60:
                problemas.append({
                    "tipo": "warning",
                    "elemento": "Title Tag",
                    "problema": f"Title muito longo ({len(title.text)} caracteres)",
                    "impacto": "Médio - Será truncado nos resultados"
                })
                score -= 5
            
            # 2. Meta Description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if not meta_desc or not meta_desc.get('content'):
                problemas.append({
                    "tipo": "critical",
                    "elemento": "Meta Description",
                    "problema": "Meta description não encontrada",
                    "impacto": "Alto - Importante para CTR"
                })
                score -= 15
            elif len(meta_desc.get('content', '')) < 120:
                problemas.append({
                    "tipo": "warning",
                    "elemento": "Meta Description",
                    "problema": f"Description muito curta ({len(meta_desc.get('content'))} caracteres)",
                    "impacto": "Médio - Ideal: 150-160 caracteres"
                })
                score -= 5
            
            # 3. Headings (H1)
            h1_tags = soup.find_all('h1')
            if len(h1_tags) == 0:
                problemas.append({
                    "tipo": "critical",
                    "elemento": "H1",
                    "problema": "Nenhuma tag H1 encontrada",
                    "impacto": "Alto - Importante para hierarquia"
                })
                score -= 10
            elif len(h1_tags) > 1:
                problemas.append({
                    "tipo": "warning",
                    "elemento": "H1",
                    "problema": f"{len(h1_tags)} tags H1 encontradas",
                    "impacto": "Médio - Recomendado apenas 1 H1"
                })
                score -= 5
            
            # 4. Meta Robots
            meta_robots = soup.find('meta', attrs={'name': 'robots'})
            if meta_robots and 'noindex' in meta_robots.get('content', '').lower():
                problemas.append({
                    "tipo": "critical",
                    "elemento": "Meta Robots",
                    "problema": "Página marcada como noindex",
                    "impacto": "Crítico - Página não será indexada"
                })
                score -= 20
            
            # 5. Canonical
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            if not canonical:
                problemas.append({
                    "tipo": "info",
                    "elemento": "Canonical",
                    "problema": "Tag canonical não encontrada",
                    "impacto": "Baixo - Recomendado para evitar conteúdo duplicado"
                })
                score -= 3
            
            # 6. Open Graph
            og_title = soup.find('meta', property='og:title')
            og_desc = soup.find('meta', property='og:description')
            og_image = soup.find('meta', property='og:image')
            
            og_missing = []
            if not og_title:
                og_missing.append("og:title")
            if not og_desc:
                og_missing.append("og:description")
            if not og_image:
                og_missing.append("og:image")
            
            if og_missing:
                problemas.append({
                    "tipo": "warning",
                    "elemento": "Open Graph",
                    "problema": f"Tags OG faltando: {', '.join(og_missing)}",
                    "impacto": "Médio - Importante para redes sociais"
                })
                score -= len(og_missing) * 3
            
            # 7. Alt Text em Imagens
            images = soup.find_all('img')
            images_sem_alt = [img for img in images if not img.get('alt')]
            if images_sem_alt:
                problemas.append({
                    "tipo": "warning",
                    "elemento": "Imagens",
                    "problema": f"{len(images_sem_alt)} de {len(images)} imagens sem alt text",
                    "impacto": "Médio - Importante para acessibilidade e SEO"
                })
                score -= min(10, len(images_sem_alt) * 2)
            
            # 8. Links internos/externos
            links = soup.find_all('a', href=True)
            internal_links = []
            external_links = []
            
            for link in links:
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')):
                    if urlparse(url).netloc in href:
                        internal_links.append(href)
                    else:
                        external_links.append(href)
                elif href.startswith('/'):
                    internal_links.append(href)
            
            # 9. Sitemap
            sitemap_urls = [
                urljoin(url, '/sitemap.xml'),
                urljoin(url, '/sitemap_index.xml')
            ]
            tem_sitemap = False
            for sitemap_url in sitemap_urls:
                try:
                    r = requests.head(sitemap_url, timeout=5)
                    if r.status_code == 200:
                        tem_sitemap = True
                        break
                except:
                    pass
            
            if not tem_sitemap:
                problemas.append({
                    "tipo": "warning",
                    "elemento": "Sitemap",
                    "problema": "Sitemap XML não encontrado",
                    "impacto": "Médio - Ajuda mecanismos de busca"
                })
                score -= 5
            
            # 10. Robots.txt
            try:
                robots_url = urljoin(url, '/robots.txt')
                r = requests.get(robots_url, timeout=5)
                tem_robots = r.status_code == 200
            except:
                tem_robots = False
            
            if not tem_robots:
                problemas.append({
                    "tipo": "info",
                    "elemento": "Robots.txt",
                    "problema": "Arquivo robots.txt não encontrado",
                    "impacto": "Baixo - Recomendado mas não obrigatório"
                })
                score -= 2
            
            # Score final
            score = max(0, score)
            
            concorrentes = self._get_competitors_examples()
            
            return {
                "status": "ok",
                "score": round(score, 2),
                "peso": self.weight,
                "erro": None,
                "detalhes": {
                    "total_problemas": len(problemas),
                    "problemas_criticos": len([p for p in problemas if p['tipo'] == 'critical']),
                    "problemas_warnings": len([p for p in problemas if p['tipo'] == 'warning']),
                    "problemas": problemas[:10],
                    "metricas": {
                        "title_length": len(title.text) if title else 0,
                        "meta_desc_length": len(meta_desc.get('content', '')) if meta_desc else 0,
                        "h1_count": len(h1_tags),
                        "images_total": len(images),
                        "images_sem_alt": len(images_sem_alt),
                        "links_internos": len(internal_links),
                        "links_externos": len(external_links),
                        "tem_sitemap": tem_sitemap,
                        "tem_robots": tem_robots
                    },
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
    
    def _get_competitors_examples(self):
        return [
            {
                "nome": "Moz",
                "url": "https://moz.com",
                "score": 98,
                "motivo": "SEO perfeito: títulos otimizados, rich snippets, schema markup completo"
            },
            {
                "nome": "HubSpot",
                "url": "https://hubspot.com",
                "score": 97,
                "motivo": "Estrutura de headings impecável, meta tags otimizadas, conteúdo semântico"
            },
            {
                "nome": "Neil Patel",
                "url": "https://neilpatel.com",
                "score": 96,
                "motivo": "URLs amigáveis, linking interno estratégico, velocidade otimizada"
            }
        ]