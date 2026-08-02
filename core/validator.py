"""
core/validator.py
Validador de URLs e dados de entrada
"""
import re
from urllib.parse import urlparse
from typing import Tuple, Optional

class Validator:
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        Valida se uma URL é válida
        
        Returns:
            Tuple[bool, Optional[str]]: (é_válida, mensagem_erro)
        """
        if not url:
            return False, "URL não pode ser vazia"
        
        # Adiciona protocolo se não existir
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            result = urlparse(url)
            
            # Verifica se tem scheme e netloc
            if not all([result.scheme, result.netloc]):
                return False, "URL inválida: falta protocolo ou domínio"
            
            # Verifica se o scheme é http ou https
            if result.scheme not in ['http', 'https']:
                return False, "URL deve usar protocolo HTTP ou HTTPS"
            
            # Verifica se o domínio tem formato válido
            domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
            if not re.match(domain_pattern, result.netloc.split(':')[0]):
                return False, "Domínio inválido"
            
            return True, None
            
        except Exception as e:
            return False, f"Erro ao validar URL: {str(e)}"
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Remove caracteres perigosos e normaliza a URL"""
        # Remove espaços
        url = url.strip()
        
        # Adiciona https se não tiver protocolo
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    @staticmethod
    def validate_plugin_result(result: dict) -> Tuple[bool, Optional[str]]:
        """
        Valida o resultado de um plugin
        
        Returns:
            Tuple[bool, Optional[str]]: (é_válido, mensagem_erro)
        """
        required_fields = ['status', 'score', 'peso']
        
        for field in required_fields:
            if field not in result:
                return False, f"Campo obrigatório ausente: {field}"
        
        # Valida status
        if result['status'] not in ['ok', 'error']:
            return False, "Status deve ser 'ok' ou 'error'"
        
        # Valida score
        try:
            score = float(result['score'])
            if not 0 <= score <= 100:
                return False, "Score deve estar entre 0 e 100"
        except (ValueError, TypeError):
            return False, "Score deve ser um número"
        
        # Valida peso
        try:
            peso = float(result['peso'])
            if peso <= 0:
                return False, "Peso deve ser maior que 0"
        except (ValueError, TypeError):
            return False, "Peso deve ser um número"
        
        return True, None
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_social_url(url: str, platform: str) -> bool:
        """Valida se URL é de uma rede social específica"""
        social_patterns = {
            'facebook': r'facebook\.com',
            'instagram': r'instagram\.com',
            'twitter': r'(twitter\.com|x\.com)',
            'linkedin': r'linkedin\.com',
            'youtube': r'youtube\.com',
            'tiktok': r'tiktok\.com'
        }
        
        pattern = social_patterns.get(platform.lower())
        if not pattern:
            return False
        
        return bool(re.search(pattern, url.lower()))