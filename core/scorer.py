"""Sistema de pontuação, cobertura e ranking."""
from __future__ import annotations

from typing import Any, Dict


class Scorer:
    def __init__(self, minimum_coverage_for_ranking: float = 80.0):
        self.minimum_coverage_for_ranking = float(minimum_coverage_for_ranking)
        self.rankings = {
            "A": (90, 100, "Excelente"),
            "B": (80, 89.999, "Muito bom"),
            "C": (70, 79.999, "Bom"),
            "D": (60, 69.999, "Regular"),
            "E": (0, 59.999, "Precisa melhorias"),
        }

    def calculate_analysis(self, plugins: Dict[str, Any]) -> Dict[str, Any]:
        total_weighted = 0.0
        expected_weight = 0.0
        available_weight = 0.0
        ok_count = 0
        error_count = 0
        not_applicable_count = 0

        for plugin_data in plugins.values():
            status = str(plugin_data.get("status", "ok"))
            weight = self._number(plugin_data.get("peso", 1), 1.0)

            if status in {"not_applicable", "disabled", "skipped"}:
                not_applicable_count += 1
                continue

            expected_weight += weight
            if status == "ok":
                score = max(0.0, min(100.0, self._number(plugin_data.get("score", 0), 0.0)))
                total_weighted += score * weight
                available_weight += weight
                ok_count += 1
            else:
                error_count += 1

        score = round(total_weighted / available_weight, 2) if available_weight else 0.0
        coverage = round((available_weight / expected_weight * 100), 2) if expected_weight else 100.0
        rankable = bool(available_weight) and coverage >= self.minimum_coverage_for_ranking
        ranking = self.get_ranking(score) if rankable else f"Inconclusivo (cobertura {coverage:.0f}%)"

        if coverage >= 95:
            confidence = "alta"
        elif coverage >= self.minimum_coverage_for_ranking:
            confidence = "média"
        else:
            confidence = "baixa"

        return {
            "score_final": score,
            "ranking": ranking,
            "coverage": coverage,
            "confidence": confidence,
            "rankable": rankable,
            "analysis_status": "complete" if error_count == 0 else "partial",
            "plugins_ok": ok_count,
            "plugins_error": error_count,
            "plugins_not_applicable": not_applicable_count,
            "available_weight": round(available_weight, 3),
            "expected_weight": round(expected_weight, 3),
        }

    def calculate_final_score(self, plugins: Dict[str, Any]) -> float:
        """Compatibilidade com chamadas antigas."""
        return float(self.calculate_analysis(plugins)["score_final"])

    def get_ranking(self, score: float) -> str:
        for rank, (minimum, maximum, description) in self.rankings.items():
            if minimum <= score <= maximum:
                return f"{rank} ({description})"
        return "E (Precisa melhorias)"

    def get_rank_letter(self, score: float) -> str:
        for rank, (minimum, maximum, _) in self.rankings.items():
            if minimum <= score <= maximum:
                return rank
        return "E"

    def calculate_category_score(self, problems: int, total: int, severity_weight: float = 1.0) -> float:
        if total == 0:
            return 100.0
        problem_rate = problems / total * 100
        return round(max(0.0, 100 - problem_rate * severity_weight), 2)

    def get_score_color(self, score: float) -> str:
        if score >= 80:
            return "success"
        if score >= 60:
            return "warning"
        return "danger"

    def compare_with_benchmark(self, score: float, benchmark: float) -> Dict[str, Any]:
        difference = score - benchmark
        percentage = difference / benchmark * 100 if benchmark > 0 else 0
        return {
            "score": score,
            "benchmark": benchmark,
            "difference": round(difference, 2),
            "percentage": round(percentage, 2),
            "status": "above" if difference > 0 else "below" if difference < 0 else "equal",
        }

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
