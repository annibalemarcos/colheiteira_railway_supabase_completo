"""
plugins/lighthouse/plugin.py
Plugin atualizado com análise completa do Lighthouse.

Correção Windows/npm global:
- tenta lighthouse, lighthouse.cmd e lighthouse.exe;
- adiciona automaticamente os caminhos comuns do npm global ao PATH;
- usa LIGHTHOUSE_BIN, se definida;
- cai para npx --yes lighthouse quando o binário global não aparece no PATH.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


class LighthousePlugin:
    def __init__(self):
        self.name = "lighthouse"
        self.description = "Análise de performance, acessibilidade e boas práticas"
        self.weight = 1.5

    def run(self, url: str) -> Dict[str, Any]:
        output_file: Optional[str] = None
        try:
            env = self._build_env()
            lighthouse_cmd = self._resolve_lighthouse_command(env)

            if not lighthouse_cmd:
                return {
                    "status": "error",
                    "score": 0,
                    "peso": self.weight,
                    "erro": (
                        "Lighthouse não foi encontrado pelo Python. Ele pode estar instalado, "
                        "mas fora do PATH desta janela. Rode `where lighthouse` e `npm prefix -g`. "
                        "Se aparecer algo como `%APPDATA%\\npm`, reabra o terminal ou use o run_dashboard.bat atualizado."
                    ),
                    "detalhes": {
                        "tentativas": self._candidate_commands(env, include_npx=True),
                        "dica_windows": "No Windows o executável costuma ser lighthouse.cmd em C:\\Users\\SEU_USUARIO\\AppData\\Roaming\\npm."
                    }
                }

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                output_file = tmp.name

            cmd = lighthouse_cmd + [
                url,
                "--output=json",
                f"--output-path={output_file}",
                "--chrome-flags=--headless --no-sandbox",
                "--quiet",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )

            if result.returncode != 0:
                stderr = (result.stderr or result.stdout or "").strip()
                return {
                    "status": "error",
                    "score": 0,
                    "peso": self.weight,
                    "erro": f"Lighthouse falhou ao executar. {stderr[:1200]}",
                    "detalhes": {
                        "comando": " ".join(cmd[:2]),
                        "returncode": result.returncode,
                    },
                }

            if not output_file or not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                return {
                    "status": "error",
                    "score": 0,
                    "peso": self.weight,
                    "erro": "Lighthouse executou, mas não gerou o JSON de saída.",
                    "detalhes": {"comando": " ".join(cmd[:2])},
                }

            with open(output_file, "r", encoding="utf-8") as f:
                lighthouse_data = json.load(f)

            categories = lighthouse_data.get("categories", {})

            # O Lighthouse 13 pode retornar score=None em algumas categorias/audits.
            # Antes isso quebrava com: "'<' not supported between instances of 'NoneType' and 'float'".
            performance = self._category_score(categories, "performance")
            accessibility = self._category_score(categories, "accessibility")
            best_practices = self._category_score(categories, "best-practices")
            seo_score = self._category_score(categories, "seo")

            valid_category_scores = [
                score for score in (performance, accessibility, best_practices, seo_score)
                if score is not None
            ]
            score_final = (sum(valid_category_scores) / len(valid_category_scores)) if valid_category_scores else 0

            audits = lighthouse_data.get("audits", {})
            metricas_performance = {
                "first_contentful_paint": self._get_metric(audits, "first-contentful-paint"),
                "speed_index": self._get_metric(audits, "speed-index"),
                "largest_contentful_paint": self._get_metric(audits, "largest-contentful-paint"),
                "time_to_interactive": self._get_metric(audits, "interactive"),
                "total_blocking_time": self._get_metric(audits, "total-blocking-time"),
                "cumulative_layout_shift": self._get_metric(audits, "cumulative-layout-shift"),
            }

            problemas = []
            if performance < 50:
                problemas.append({
                    "categoria": "Performance",
                    "severidade": "critical",
                    "problema": f"Score muito baixo: {performance:.0f}/100",
                    "sugestao": "Otimize imagens, minimize CSS/JS, use CDN",
                })

            if accessibility < 80:
                problemas.append({
                    "categoria": "Acessibilidade",
                    "severidade": "warning",
                    "problema": f"Score abaixo do ideal: {accessibility:.0f}/100",
                    "sugestao": "Adicione alt text, melhore contraste, use ARIA labels",
                })

            if best_practices < 80:
                problemas.append({
                    "categoria": "Boas Práticas",
                    "severidade": "warning",
                    "problema": f"Score abaixo do ideal: {best_practices:.0f}/100",
                    "sugestao": "Use HTTPS, evite bibliotecas vulneráveis, otimize recursos",
                })

            oportunidades = []
            for audit_id, audit in audits.items():
                audit_score = self._safe_float(audit.get("score"), default=1.0)
                details = audit.get("details") or {}
                if details and audit_score < 0.9:
                    savings = self._safe_float(details.get("overallSavingsMs"), default=0.0)
                    if savings > 500:
                        oportunidades.append({
                            "titulo": audit.get("title", audit_id),
                            "descricao": audit.get("description", ""),
                            "economia_ms": round(savings, 2),
                        })

            oportunidades.sort(key=lambda x: x["economia_ms"], reverse=True)
            concorrentes = self._get_competitors_examples()

            return {
                "status": "ok",
                "score": round(score_final, 2),
                "peso": self.weight,
                "erro": None,
                "detalhes": {
                    "scores": {
                        "performance": round(performance, 2),
                        "accessibility": round(accessibility, 2),
                        "best_practices": round(best_practices, 2),
                        "seo": round(seo_score, 2),
                    },
                    "metricas_performance": metricas_performance,
                    "problemas": problemas,
                    "oportunidades": oportunidades[:5],
                    "concorrentes": concorrentes,
                    "lighthouse_bin": " ".join(lighthouse_cmd),
                },
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "score": 0,
                "peso": self.weight,
                "erro": "Timeout ao executar Lighthouse (>120s)",
                "detalhes": {},
            }
        except Exception as e:
            return {
                "status": "error",
                "score": 0,
                "peso": self.weight,
                "erro": str(e),
                "detalhes": {},
            }
        finally:
            if output_file and os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                except OSError:
                    pass

    def _build_env(self) -> Dict[str, str]:
        """Monta um PATH mais esperto para achar binários globais do npm no Windows."""
        env = os.environ.copy()
        path_parts = []

        for var in ("APPDATA", "LOCALAPPDATA"):
            value = env.get(var)
            if value:
                path_parts.append(str(Path(value) / "npm"))

        program_files = env.get("ProgramFiles")
        if program_files:
            path_parts.append(str(Path(program_files) / "nodejs"))

        npm_prefix = self._npm_prefix(env)
        if npm_prefix:
            path_parts.append(npm_prefix)

        existing_path = env.get("PATH", "")
        unique_parts = []
        seen = set()
        for part in path_parts + existing_path.split(os.pathsep):
            if not part:
                continue
            normalized = part.lower()
            if normalized not in seen:
                unique_parts.append(part)
                seen.add(normalized)

        env["PATH"] = os.pathsep.join(unique_parts)
        return env

    def _npm_prefix(self, env: Dict[str, str]) -> Optional[str]:
        for npm_cmd in ("npm", "npm.cmd"):
            npm_path = shutil.which(npm_cmd, path=env.get("PATH")) or npm_cmd
            try:
                result = subprocess.run(
                    [npm_path, "prefix", "-g"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    env=env,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except Exception:
                continue
        return None

    def _candidate_commands(self, env: Dict[str, str], include_npx: bool = False) -> List[List[str]]:
        candidates: List[List[str]] = []

        configured_bin = env.get("LIGHTHOUSE_BIN")
        if configured_bin:
            candidates.append([configured_bin])

        for name in ("lighthouse", "lighthouse.cmd", "lighthouse.exe"):
            resolved = shutil.which(name, path=env.get("PATH"))
            if resolved:
                candidates.append([resolved])
            candidates.append([name])

        npm_prefix = self._npm_prefix(env)
        if npm_prefix:
            for name in ("lighthouse.cmd", "lighthouse.exe", "lighthouse"):
                direct = str(Path(npm_prefix) / name)
                if direct not in [cmd[0] for cmd in candidates]:
                    candidates.append([direct])

        if include_npx:
            for name in ("npx", "npx.cmd"):
                resolved = shutil.which(name, path=env.get("PATH"))
                if resolved:
                    candidates.append([resolved, "--yes", "lighthouse"])
                candidates.append([name, "--yes", "lighthouse"])

        deduped: List[List[str]] = []
        seen = set()
        for candidate in candidates:
            key = tuple(candidate)
            if key not in seen:
                deduped.append(candidate)
                seen.add(key)
        return deduped

    def _resolve_lighthouse_command(self, env: Dict[str, str]) -> Optional[List[str]]:
        """Encontra um comando funcional do Lighthouse sem travar o app.

        Primeiro testa os binários diretos (`lighthouse`, `lighthouse.cmd`, etc.).
        Só depois tenta `npx`, porque `npx --yes` pode tentar baixar pacote e
        demorar quando a rede/npm está fazendo cosplay de tartaruga.
        """
        direct_candidates = self._candidate_commands(env, include_npx=False)
        npx_candidates = [
            c for c in self._candidate_commands(env, include_npx=True)
            if c not in direct_candidates
        ]

        for candidate in direct_candidates:
            try:
                result = subprocess.run(
                    candidate + ["--version"],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    env=env,
                )
                if result.returncode == 0:
                    return candidate
            except Exception:
                continue

        for candidate in npx_candidates:
            try:
                result = subprocess.run(
                    candidate + ["--version"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    env=env,
                )
                if result.returncode == 0:
                    return candidate
            except Exception:
                continue

        return None


    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Converte números do Lighthouse com proteção contra None/string."""
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _category_score(self, categories: Dict[str, Any], category_id: str) -> float:
        """Retorna score da categoria em escala 0-100, aceitando score None."""
        category = categories.get(category_id) or {}
        return self._safe_float(category.get("score"), default=0.0) * 100

    def _get_metric(self, audits: dict, metric_id: str) -> dict:
        """Extrai uma métrica específica dos audits."""
        audit = audits.get(metric_id, {})
        return {
            "value": audit.get("numericValue", 0),
            "display": audit.get("displayValue", "N/A"),
            "score": audit.get("score", 0),
        }

    def _get_competitors_examples(self):
        return [
            {
                "nome": "Google",
                "url": "https://google.com",
                "performance": 99,
                "motivo": "Infraestrutura global, otimização extrema, recursos mínimos",
            },
            {
                "nome": "Vercel",
                "url": "https://vercel.com",
                "performance": 98,
                "motivo": "CDN edge, code splitting, pre-rendering, image optimization",
            },
            {
                "nome": "Cloudflare",
                "url": "https://cloudflare.com",
                "performance": 97,
                "motivo": "Edge computing, automatic optimization, smart caching",
            },
        ]
