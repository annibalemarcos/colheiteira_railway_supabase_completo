"""
plugins/social_media/plugin.py
Plugin para análise de redes sociais
"""
from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

class SocialMediaPlugin:
    def __init__(self):
        self.name = "social_media"
        self.description = "Analisa presença e qualidade das redes sociais"
        self.weight = 1.4
        
        self.social_patterns = {
            'facebook': r'facebook\.com/([^/\s]+)',
            'instagram': r'instagram\.com/([^/\s]+)',
            'twitter': r'twitter\.com/([^/\s]+)',
            'linkedin': r'linkedin\.com/(?:company|in)/([^/\s]+)',
            'youtube': r'youtube\.com/(?:c|channel|user)/([^/\s]+)',
            'tiktok': r'tiktok\.com/@([^/\s]+)'
        }
    
    def run(self, url: str) -> Dict[str, Any]:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontra links de redes sociais
            social_links = self._find_social_links(soup, url)
            
            # Analisa cada rede social
            analises = {}
            for rede, link in social_links.items():
                analise = self._analyze_social_profile(rede, link)
                analises[rede] = analise
            
            # Cálculo do score
            score = self._calculate_score(social_links, analises)
            
            concorrentes = self._get_competitors_examples()
            
            return {
                "status": "ok",
                "score": round(score, 2),
                "peso": self.weight,
                "erro": None,
                "detalhes": {
                    "redes_encontradas": len(social_links),
                    "redes": social_links,
                    "analises": analises,
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
    
    def _find_social_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        """Encontra todos os links de redes sociais"""
        links = {}
        
        for link in soup.find_all(['a', 'link']):
            href = link.get('href', '')
            
            for rede, pattern in self.social_patterns.items():
                if re.search(pattern, href):
                    links[rede] = href
                    break
        
        return links
    
    def _analyze_social_profile(self, rede: str, url: str) -> Dict[str, Any]:
        """Analisa o perfil de uma rede social"""
        try:
            # Nota: Em produção, você usaria APIs oficiais
            # Aqui é uma análise simplificada
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Busca por metatags de imagem
            og_image = soup.find('meta', property='og:image')
            profile_image = og_image['content'] if og_image else None
            
            # Análise básica
            problemas = []
            
            if not profile_image:
                problemas.append("Sem imagem de perfil detectada")
            
            # Verifica atividade recente (simulado)
            score_atividade = 70  # Em produção, verificaria posts recentes
            
            return {
                'acessivel': True,
                'imagem_perfil': bool(profile_image),
                'score_atividade': score_atividade,
                'problemas': problemas,
                'url': url
            }
        except Exception as e:
            return {
                'acessivel': False,
                'erro': str(e),
                'problemas': ['Não foi possível acessar o perfil']
            }
    
    def _calculate_score(self, links: Dict, analises: Dict) -> float:
        """Calcula score baseado na presença e qualidade"""
        # Pontos por presença
        score = len(links) * 15
        
        # Pontos por qualidade
        for rede, analise in analises.items():
            if analise.get('acessivel'):
                score += 10
            if analise.get('imagem_perfil'):
                score += 5
            score += analise.get('score_atividade', 0) * 0.2
        
        return min(100, score)
    
    def _get_competitors_examples(self):
        return [
            {
                "nome": "Nike",
                "redes": 6,
                "score": 98,
                "motivo": "Presença ativa em todas plataformas, conteúdo de alta qualidade, engajamento alto"
            },
            {
                "nome": "Netflix",
                "redes": 6,
                "score": 97,
                "motivo": "Estratégia de conteúdo adaptada por plataforma, posts diários, design consistente"
            },
            {
                "nome": "Coca-Cola",
                "redes": 5,
                "score": 96,
                "motivo": "Campanhas integradas, identidade visual forte, alta frequência de posts"
            }
        ]