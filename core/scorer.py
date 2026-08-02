"""
core/scorer.py
Sistema de pontuação e ranking
"""
from typing import Dict, Any

class Scorer:
    def __init__(self):
        self.rankings = {
            'A': (90, 100, 'Excelente'),
            'B': (80, 89, 'Muito bom'),
            'C': (70, 79, 'Bom'),
            'D': (60, 69, 'Regular'),
            'E': (0, 59, 'Precisa melhorias')
        }
    
    def calculate_final_score(self, plugins: Dict[str, Any]) -> float:
        """
        Calcula o score final ponderado
        Formula: Σ(score * peso) / Σ(pesos)
        """
        total_weighted = 0
        total_weight = 0
        
        for plugin_name, plugin_data in plugins.items():
            if plugin_data['status'] == 'ok':
                score = plugin_data.get('score', 0)
                weight = plugin_data.get('peso', 1)
                
                total_weighted += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0
        
        return round(total_weighted / total_weight, 2)
    
    def get_ranking(self, score: float) -> str:
        """Retorna o ranking baseado no score"""
        for rank, (min_score, max_score, description) in self.rankings.items():
            if min_score <= score <= max_score:
                return f"{rank} ({description})"
        
        return "E (Precisa melhorias)"
    
    def get_rank_letter(self, score: float) -> str:
        """Retorna apenas a letra do ranking"""
        for rank, (min_score, max_score, _) in self.rankings.items():
            if min_score <= score <= max_score:
                return rank
        return "E"
    
    def calculate_category_score(self, problems: int, total: int, severity_weight: float = 1.0) -> float:
        """
        Calcula score de uma categoria baseado em problemas encontrados
        
        Args:
            problems: Número de problemas encontrados
            total: Total de itens analisados
            severity_weight: Peso da severidade (1.0 = normal, 2.0 = dobra impacto)
        
        Returns:
            Score de 0 a 100
        """
        if total == 0:
            return 100
        
        problem_rate = (problems / total) * 100
        weighted_impact = problem_rate * severity_weight
        
        score = max(0, 100 - weighted_impact)
        return round(score, 2)
    
    def get_score_color(self, score: float) -> str:
        """Retorna a cor apropriada para o score"""
        if score >= 80:
            return 'success'
        elif score >= 60:
            return 'warning'
        else:
            return 'danger'
    
    def compare_with_benchmark(self, score: float, benchmark: float) -> Dict[str, Any]:
        """Compara score com benchmark"""
        difference = score - benchmark
        percentage_diff = (difference / benchmark * 100) if benchmark > 0 else 0
        
        return {
            'score': score,
            'benchmark': benchmark,
            'difference': round(difference, 2),
            'percentage': round(percentage_diff, 2),
            'status': 'above' if difference > 0 else 'below' if difference < 0 else 'equal'
        }