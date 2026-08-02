"""
plugins/imagens/plugin.py
Plugin para análise de qualidade de imagens
"""
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

class ImagensPlugin:
    def __init__(self):
        self.name = "imagens"
        self.description = "Analisa qualidade e problemas com imagens"
        self.weight = 1.6
    
    def run(self, url: str) -> Dict[str, Any]:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Coleta todas as imagens
            imagens = []
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    imagens.append({
                        'url': urljoin(url, src),
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    })
            
            problemas = {
                'sem_alt': [],
                'baixa_qualidade': [],
                'muito_grandes': [],
                'faltando': []
            }
            
            # Analisa cada imagem
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_img = {executor.submit(self._analyze_image, img): img for img in imagens[:50]}
                
                for future in as_completed(future_to_img):
                    img = future_to_img[future]
                    try:
                        resultado = future.result()
                        
                        # Sem alt text
                        if not img['alt']:
                            problemas['sem_alt'].append(img)
                        
                        # Problemas de qualidade
                        if resultado:
                            if resultado.get('erro'):
                                problemas['faltando'].append({**img, **resultado})
                            elif resultado.get('tamanho', 0) > 500000:  # > 500KB
                                problemas['muito_grandes'].append({**img, **resultado})
                            elif resultado.get('qualidade') == 'baixa':
                                problemas['baixa_qualidade'].append({**img, **resultado})
                                
                    except Exception as e:
                        problemas['faltando'].append({**img, 'erro': str(e)})
            
            # Cálculo do score
            total_imgs = len(imagens)
            total_problemas = sum(len(p) for p in problemas.values())
            taxa_problemas = total_problemas / max(total_imgs, 1) * 100
            
            score = max(0, 100 - (taxa_problemas * 3))
            
            concorrentes = self._get_competitors_examples()
            
            return {
                "status": "ok",
                "score": round(score, 2),
                "peso": self.weight,
                "erro": None,
                "detalhes": {
                    "total_imagens": total_imgs,
                    "sem_alt": len(problemas['sem_alt']),
                    "baixa_qualidade": len(problemas['baixa_qualidade']),
                    "muito_grandes": len(problemas['muito_grandes']),
                    "faltando": len(problemas['faltando']),
                    "problemas": {
                        k: v[:5] for k, v in problemas.items()
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
    
    def _analyze_image(self, img_data: dict) -> dict:
        """Analisa uma imagem específica"""
        try:
            response = requests.get(img_data['url'], timeout=5)
            image = Image.open(BytesIO(response.content))
            
            width, height = image.size
            tamanho = len(response.content)
            
            # Determina qualidade baseada em resolução
            pixels = width * height
            qualidade = 'alta' if pixels > 1000000 else 'media' if pixels > 250000 else 'baixa'
            
            return {
                'largura': width,
                'altura': height,
                'tamanho': tamanho,
                'formato': image.format,
                'qualidade': qualidade
            }
        except Exception as e:
            return {'erro': str(e)}
    
    def _get_competitors_examples(self):
        return [
            {
                "nome": "Unsplash",
                "url": "https://unsplash.com",
                "qualidade": 98,
                "motivo": "Apenas imagens de alta resolução, WebP otimizado, lazy loading"
            },
            {
                "nome": "Adobe Stock",
                "url": "https://stock.adobe.com",
                "qualidade": 97,
                "motivo": "Controle de qualidade rigoroso, múltiplos formatos e tamanhos"
            },
            {
                "nome": "Pexels",
                "url": "https://pexels.com",
                "qualidade": 96,
                "motivo": "Curadoria de imagens, compressão inteligente, CDN global"
            }
        ]