"""Plugin Lighthouse estabilizado para execução local e Railway."""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class LighthousePlugin:
    def __init__(self):
        self.name = "lighthouse"
        self.description = "Análise de performance, acessibilidade e boas práticas"
        self.weight = 2.4
        self.config: Dict[str, Any] = {}

    def run(self, url: str) -> Dict[str, Any]:
        env = self._build_env()
        lighthouse_cmd = self._resolve_lighthouse_command(env)
        if not lighthouse_cmd:
            return self._error(
                "Lighthouse não foi encontrado pelo Python.",
                {"tentativas": self._candidate_commands(env, include_npx=True)},
            )

        timeout = max(90, int(self.config.get("timeout_seconds", os.getenv("LIGHTHOUSE_TIMEOUT", "180"))))
        attempts = max(1, min(int(self.config.get("retry_attempts", 2)), 3))
        last_error = "Falha desconhecida do Lighthouse."
        last_details: Dict[str, Any] = {}

        for attempt in range(1, attempts + 1):
            try:
                data, command = self._execute(url, lighthouse_cmd, env, timeout)
                result = self._parse_report(data, command)
                result["detalhes"]["tentativa"] = attempt
                result["detalhes"]["tentativas_maximas"] = attempts
                return result
            except TimeoutError as exc:
                last_error = str(exc)
                last_details = {"tentativa": attempt, "timeout_seconds": timeout}
            except RuntimeError as exc:
                last_error = str(exc)
                last_details = {"tentativa": attempt}
            except Exception as exc:
                last_error = str(exc)
                last_details = {"tentativa": attempt}

            if attempt < attempts:
                time.sleep(2.0)

        return self._error(last_error, last_details)

    def _execute(
        self,
        url: str,
        lighthouse_cmd: List[str],
        env: Dict[str, str],
        timeout: int,
    ) -> Tuple[Dict[str, Any], str]:
        with tempfile.TemporaryDirectory(prefix="colheiteira_lighthouse_") as temp_dir:
            output_file = Path(temp_dir) / "report.json"
            profile_dir = Path(temp_dir) / "chrome-profile"
            categories = self.config.get("categories") or ["performance", "accessibility", "best-practices", "seo"]
            category_arg = ",".join(str(item) for item in categories)
            chrome_flags = " ".join([
                "--headless=new",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-renderer-backgrounding",
                "--disable-background-timer-throttling",
                f"--user-data-dir={profile_dir}",
            ])

            cmd = lighthouse_cmd + [
                url,
                "--output=json",
                f"--output-path={output_file}",
                f"--only-categories={category_arg}",
                "--max-wait-for-load=90000",
                f"--chrome-flags={chrome_flags}",
                "--quiet",
            ]
            if str(self.config.get("device", "mobile")).lower() == "desktop":
                cmd.append("--preset=desktop")

            returncode, stdout, stderr = self._run_process(cmd, env=env, timeout=timeout)
            if returncode != 0:
                message = (stderr or stdout or "").strip()
                raise RuntimeError(f"Lighthouse falhou ao executar. {message[:1400]}")
            if not output_file.exists() or output_file.stat().st_size == 0:
                raise RuntimeError("Lighthouse executou, mas não gerou o JSON de saída.")

            try:
                data = json.loads(output_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"JSON inválido gerado pelo Lighthouse: {exc}") from exc
            return data, " ".join(cmd[:2])

    def _run_process(self, cmd: List[str], *, env: Dict[str, str], timeout: int) -> Tuple[int, str, str]:
        kwargs: Dict[str, Any] = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "env": env,
        }
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            kwargs["start_new_session"] = True

        process = subprocess.Popen(cmd, **kwargs)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode, stdout, stderr
        except subprocess.TimeoutExpired as exc:
            self._terminate_process_tree(process)
            stdout, stderr = process.communicate()
            raise TimeoutError(f"Timeout ao executar Lighthouse (>{timeout}s)") from exc

    @staticmethod
    def _terminate_process_tree(process: subprocess.Popen) -> None:
        try:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def _parse_report(self, data: Dict[str, Any], command: str) -> Dict[str, Any]:
        categories = data.get("categories") or {}
        scores = {
            "performance": self._category_score(categories, "performance"),
            "accessibility": self._category_score(categories, "accessibility"),
            "best_practices": self._category_score(categories, "best-practices"),
            "seo": self._category_score(categories, "seo"),
        }
        valid = {key: value for key, value in scores.items() if value is not None}
        if not valid:
            raise RuntimeError("O Lighthouse não retornou scores válidos.")

        weights = {"performance": 0.35, "accessibility": 0.25, "best_practices": 0.20, "seo": 0.20}
        denominator = sum(weights[key] for key in valid)
        final_score = sum(valid[key] * weights[key] for key in valid) / denominator

        audits = data.get("audits") or {}
        metrics = {
            "first_contentful_paint": self._metric(audits, "first-contentful-paint"),
            "speed_index": self._metric(audits, "speed-index"),
            "largest_contentful_paint": self._metric(audits, "largest-contentful-paint"),
            "time_to_interactive": self._metric(audits, "interactive"),
            "total_blocking_time": self._metric(audits, "total-blocking-time"),
            "cumulative_layout_shift": self._metric(audits, "cumulative-layout-shift"),
        }

        problems = []
        thresholds = {
            "performance": (50, "Performance", "critical", "Otimize imagens, JavaScript, CSS e cache."),
            "accessibility": (80, "Acessibilidade", "warning", "Revise contraste, rótulos, foco e textos alternativos."),
            "best_practices": (80, "Boas práticas", "warning", "Revise HTTPS, erros do navegador e bibliotecas."),
            "seo": (80, "SEO Lighthouse", "warning", "Revise indexação e elementos básicos de descoberta."),
        }
        for key, (threshold, label, severity, suggestion) in thresholds.items():
            value = valid.get(key)
            if value is not None and value < threshold:
                problems.append({
                    "categoria": label,
                    "severidade": severity,
                    "problema": f"Score abaixo do ideal: {value:.0f}/100",
                    "sugestao": suggestion,
                })

        opportunities = []
        for audit_id, audit in audits.items():
            details = audit.get("details") or {}
            audit_score = self._safe_float(audit.get("score"), 1.0)
            savings = self._safe_float(details.get("overallSavingsMs"), 0.0)
            if audit_score < 0.9 and savings > 500:
                opportunities.append({
                    "titulo": audit.get("title", audit_id),
                    "descricao": audit.get("description", ""),
                    "economia_ms": round(savings, 2),
                })
        opportunities.sort(key=lambda item: item["economia_ms"], reverse=True)

        return {
            "status": "ok",
            "score": round(final_score, 2),
            "peso": self.weight,
            "erro": None,
            "detalhes": {
                "scores": {key: round(value, 2) if value is not None else None for key, value in scores.items()},
                "metricas_performance": metrics,
                "problemas": problems,
                "oportunidades": opportunities[:5],
                "lighthouse_bin": command,
                "versao_lighthouse": data.get("lighthouseVersion"),
                "url_final": data.get("finalDisplayedUrl") or data.get("finalUrl"),
            },
        }

    def _build_env(self) -> Dict[str, str]:
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

        existing = env.get("PATH", "")
        unique = []
        seen = set()
        for part in path_parts + existing.split(os.pathsep):
            if part and part.lower() not in seen:
                unique.append(part)
                seen.add(part.lower())
        env["PATH"] = os.pathsep.join(unique)
        return env

    def _npm_prefix(self, env: Dict[str, str]) -> Optional[str]:
        for npm_cmd in ("npm", "npm.cmd"):
            resolved = shutil.which(npm_cmd, path=env.get("PATH")) or npm_cmd
            try:
                result = subprocess.run([resolved, "prefix", "-g"], capture_output=True, text=True, timeout=12, env=env)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except Exception:
                continue
        return None

    def _candidate_commands(self, env: Dict[str, str], include_npx: bool = False) -> List[List[str]]:
        candidates: List[List[str]] = []
        configured = env.get("LIGHTHOUSE_BIN")
        if configured:
            candidates.append([configured])
        for name in ("lighthouse", "lighthouse.cmd", "lighthouse.exe"):
            resolved = shutil.which(name, path=env.get("PATH"))
            if resolved:
                candidates.append([resolved])
            candidates.append([name])
        npm_prefix = self._npm_prefix(env)
        if npm_prefix:
            for name in ("lighthouse", "lighthouse.cmd", "lighthouse.exe"):
                candidates.append([str(Path(npm_prefix) / name)])
        if include_npx:
            for name in ("npx", "npx.cmd"):
                resolved = shutil.which(name, path=env.get("PATH"))
                if resolved:
                    candidates.append([resolved, "--yes", "lighthouse"])
                candidates.append([name, "--yes", "lighthouse"])

        deduped = []
        seen = set()
        for item in candidates:
            key = tuple(item)
            if key not in seen:
                deduped.append(item)
                seen.add(key)
        return deduped

    def _resolve_lighthouse_command(self, env: Dict[str, str]) -> Optional[List[str]]:
        direct = self._candidate_commands(env, include_npx=False)
        all_candidates = self._candidate_commands(env, include_npx=True)
        for candidate in direct + [item for item in all_candidates if item not in direct]:
            try:
                result = subprocess.run(candidate + ["--version"], capture_output=True, text=True, timeout=15, env=env)
                if result.returncode == 0:
                    return candidate
            except Exception:
                continue
        return None

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return default if value is None else float(value)
        except (TypeError, ValueError):
            return default

    def _category_score(self, categories: Dict[str, Any], category_id: str) -> Optional[float]:
        category = categories.get(category_id)
        if not category or category.get("score") is None:
            return None
        return self._safe_float(category.get("score")) * 100

    def _metric(self, audits: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
        audit = audits.get(metric_id) or {}
        return {
            "value": audit.get("numericValue"),
            "display": audit.get("displayValue", "N/A"),
            "score": audit.get("score"),
        }

    def _error(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "status": "error",
            "score": 0,
            "peso": self.weight,
            "erro": message,
            "detalhes": details or {},
        }
