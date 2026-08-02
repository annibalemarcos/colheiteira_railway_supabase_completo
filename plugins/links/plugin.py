"""
plugins/links/plugin.py
Plugin para detectar links quebrados
"""
from typing import Dict, Any, List
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

class LinksPlugin:
    def __init__(self):
        self.name = "links"
        self.description = "Verifica links quebrados e problemas de navegação"
        self.weight = 1.8
    
    def run(self, url: str) -> Dict[str, Any]:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Coleta todos os links
            links = []
            for tag in soup.find_all(['a', 'link', 'script', 'img']):
                href = tag.get('href') or tag.get('src')
                if href:
                    absolute_url = urljoin(url, href)
                    links.append({
                        'url': absolute_url,
                        'tipo': tag.name,
                        'texto': tag.get_text()[:50] if tag.name == 'a' else tag.get('alt', '')
                    })
            
            # Verifica status dos links
            links_quebrados = []
            links_lentos = []
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_link = {executor.submit(self._check_link, link['url']): link for link in links[:100]}
                
                for future in as_completed(future_to_link):
                    link = future_to_link[future]
                    try:
                        status, tempo = future.result()
                        if status >= 400:
                            links_quebrados.append({
                                **link,
                                'status': status,
                                'tempo': tempo
                            })
                        elif tempo > 3:
                            links_lentos.append({
                                **link,
                                'status': status,
                                'tempo': tempo
                            })
                    except Exception as e:
                        links_quebrados.append({
                            **link,
                            'status': 'error',
                            'erro': str(e)
                        })
            
            # Cálculo do score
            total_links = len(links)
            taxa_quebrados = len(links_quebrados) / max(total_links, 1) * 100
            taxa_lentos = len(links_lentos) / max(total_links, 1) * 100
            
            score = max(0, 100 - (taxa_quebrados * 5) - (taxa_lentos * 2))
            
            concorrentes = self._get_competitors_examples()
            
            return {
                "status": "ok",
                "score": round(score, 2),
                "peso": self.weight,
                "erro": None,
                "detalhes": {
                    "total_links": total_links,
                    "links_quebrados": len(links_quebrados),
                    "links_lentos": len(links_lentos),
                    "taxa_quebrados": round(taxa_quebrados, 2),
                    "problemas": links_quebrados[:10],
                    "lentos": links_lentos[:5],
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
    
    def _check_link(self, url: str) -> tuple:
        """Verifica o status de um link"""
        import time
        start = time.time()
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            tempo = time.time() - start
            return response.status_code, tempo
        except:
            try:
                response = requests.get(url, timeout=5)
                tempo = time.time() - start
                return response.status_code, tempo
            except Exception as e:
                tempo = time.time() - start
                return 500, tempo
    
    def _get_competitors_examples(self):
        return [
            {
                "nome": "Apple",
                "url": "https://apple.com",
                "taxa_quebrados": 0,
                "motivo": "Monitoramento 24/7 e testes automatizados continuos"
            },
            {
                "nome": "Google",
                "url": "https://google.com",
                "taxa_quebrados": 0,
                "motivo": "Sistema de CI/CD com validação de links antes do deploy"
            },
            {
                "nome": "Microsoft",
                "url": "https://microsoft.com",
                "taxa_quebrados": 0.1,
                "motivo": "Ferramentas internas de link checking e alertas automáticos"
            }
        ]