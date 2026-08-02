"""
server/app.py
Dashboard Flask do Colheiteira.

Roda na porta 5840:
    python server/app.py
"""
from __future__ import annotations

import hmac
import importlib.util
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

from flask import Flask, jsonify, redirect, render_template, request, send_file, session, url_for

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.analyzer import normalize_url, run_analysis  # noqa: E402
from core.scorer import Scorer  # noqa: E402
from core.storage import ResultStorage  # noqa: E402

OUTPUT_DIR = BASE_DIR / "output"
HISTORY_DIR = OUTPUT_DIR / "history"
CONFIG_FILE = BASE_DIR / "config" / "config.json"

storage = ResultStorage(BASE_DIR, OUTPUT_DIR)

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static") if (BASE_DIR / "static").exists() else None,
)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "000000")
COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "").strip().lower() in {"1", "true", "yes", "on"}
if not os.getenv("SESSION_COOKIE_SECURE") and os.getenv("RAILWAY_ENVIRONMENT"):
    COOKIE_SECURE = True

app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "colheiteira-local-secret-change-in-production"),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=COOKIE_SECURE,
)

jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()

DEFAULT_BULK_SETTINGS = {
    "min_delay": 8.0,
    "max_delay": 25.0,
    "max_urls": 30,
    "stop_on_error": False,
}

PUBLIC_ENDPOINTS = {"login", "health", "static"}


def is_safe_next_url(target: str) -> bool:
    """Aceita apenas caminhos internos para evitar redirecionamento aberto."""
    if not target:
        return False
    parsed = urlsplit(target)
    return not parsed.scheme and not parsed.netloc and target.startswith("/")


@app.before_request
def require_login():
    endpoint = request.endpoint or ""
    if endpoint in PUBLIC_ENDPOINTS or session.get("authenticated") is True:
        return None

    if request.path.startswith("/api/"):
        return jsonify({"error": "Autenticação necessária."}), 401

    next_url = request.full_path if request.query_string else request.path
    return redirect(url_for("login", next=next_url))


@app.after_request
def disable_sensitive_caching(response):
    if request.endpoint != "static" and request.path != "/health":
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


def now_iso() -> str:
    return datetime.now().isoformat()


def read_json_file(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def clamp_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def bulk_settings_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw = payload.get("settings") or {}
    min_delay = clamp_float(raw.get("min_delay"), DEFAULT_BULK_SETTINGS["min_delay"], 3.0, 600.0)
    max_delay = clamp_float(raw.get("max_delay"), DEFAULT_BULK_SETTINGS["max_delay"], 3.0, 900.0)
    if max_delay < min_delay:
        min_delay, max_delay = max_delay, min_delay

    return {
        "min_delay": round(min_delay, 2),
        "max_delay": round(max_delay, 2),
        "max_urls": clamp_int(raw.get("max_urls"), DEFAULT_BULK_SETTINGS["max_urls"], 1, 100),
        "stop_on_error": bool(raw.get("stop_on_error", DEFAULT_BULK_SETTINGS["stop_on_error"])),
    }


def parse_bulk_urls(raw_urls: Any, *, max_urls: int) -> List[str]:
    if isinstance(raw_urls, str):
        chunks = re.split(r"[\n,;\t]+", raw_urls)
    elif isinstance(raw_urls, list):
        chunks = []
        for item in raw_urls:
            chunks.extend(re.split(r"[\n,;\t]+", str(item)))
    else:
        chunks = []

    urls: List[str] = []
    seen = set()
    errors: List[str] = []

    for chunk in chunks:
        raw = chunk.strip()
        if not raw:
            continue
        try:
            url = normalize_url(raw)
        except Exception as exc:
            errors.append(f"{raw}: {exc}")
            continue
        key = url.lower().rstrip("/")
        if key not in seen:
            seen.add(key)
            urls.append(url)
        if len(urls) >= max_urls:
            break

    if not urls:
        if errors:
            raise ValueError("Nenhuma URL válida encontrada. Erros: " + " | ".join(errors[:5]))
        raise ValueError("Nenhuma URL válida encontrada.")

    return urls


def add_log(job_id: str, message: str, level: str = "info") -> None:
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message,
    }
    with jobs_lock:
        job = jobs.get(job_id)
        if job is not None:
            job.setdefault("logs", []).append(entry)
            job["updated_at"] = now_iso()


def job_public(job: Dict[str, Any]) -> Dict[str, Any]:
    result = job.get("result") or {}
    return {
        "id": job.get("id"),
        "mode": job.get("mode", "single"),
        "url": job.get("url"),
        "urls": job.get("urls", []),
        "status": job.get("status"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "ended_at": job.get("ended_at"),
        "updated_at": job.get("updated_at"),
        "error": job.get("error"),
        "logs": job.get("logs", []),
        "result": result,
        "settings": job.get("settings", {}),
        "total": job.get("total", 1),
        "completed": job.get("completed", 0),
        "current_index": job.get("current_index", 0),
        "current_url": job.get("current_url"),
        "site_results": job.get("site_results", []),
        "summary": {
            "score_final": result.get("score_final"),
            "ranking": result.get("ranking"),
            "arquivo_resultado": result.get("arquivo_resultado"),
            "arquivo_historico": result.get("arquivo_historico"),
        },
    }


def result_summary(path: Path) -> Dict[str, Any]:
    try:
        data = read_json_file(path)
        plugins = data.get("plugins", {})
        ok_count = sum(1 for item in plugins.values() if item.get("status") == "ok")
        error_count = sum(1 for item in plugins.values() if item.get("status") == "error")
        bulk = data.get("bulk") or {}
        return {
            "file": path.name,
            "path": str(path.relative_to(BASE_DIR)),
            "mode": data.get("mode", "single"),
            "url": data.get("url") or bulk.get("label"),
            "score_final": data.get("score_final"),
            "ranking": data.get("ranking"),
            "inicio": data.get("inicio"),
            "fim": data.get("fim"),
            "plugins_total": len(plugins),
            "plugins_ok": ok_count,
            "plugins_error": error_count,
            "sites_total": bulk.get("total"),
            "sites_ok": bulk.get("ok"),
            "sites_error": bulk.get("error"),
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }
    except Exception as exc:
        return {
            "file": path.name,
            "path": str(path.relative_to(BASE_DIR)),
            "error": str(exc),
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }


def lighthouse_diagnostic() -> Dict[str, Any]:
    """Roda o mesmo resolvedor usado pelo plugin Lighthouse."""
    plugin_file = BASE_DIR / "plugins" / "lighthouse" / "plugin.py"
    if not plugin_file.exists():
        return {"ok": False, "error": f"Plugin não encontrado: {plugin_file}"}

    try:
        spec = importlib.util.spec_from_file_location("colheiteira_lighthouse_plugin_diag", plugin_file)
        if not spec or not spec.loader:
            return {"ok": False, "error": "Não foi possível carregar o plugin Lighthouse."}
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin = module.LighthousePlugin()
        env = plugin._build_env()
        cmd = plugin._resolve_lighthouse_command(env)
        candidates = [" ".join(c) for c in plugin._candidate_commands(env, include_npx=True)]
        npm_prefix = plugin._npm_prefix(env)
        path_head = env.get("PATH", "").split(os.pathsep)[:10]

        if not cmd:
            return {
                "ok": False,
                "error": "Lighthouse não foi encontrado pelo processo Flask/Python.",
                "npm_prefix": npm_prefix,
                "path_head": path_head,
                "candidates": candidates,
            }

        version_result = subprocess.run(
            cmd + ["--version"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        version = (version_result.stdout or version_result.stderr or "").strip()
        return {
            "ok": version_result.returncode == 0,
            "command": " ".join(cmd),
            "version": version,
            "returncode": version_result.returncode,
            "npm_prefix": npm_prefix,
            "path_head": path_head,
            "candidates": candidates,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def run_job(job_id: str, url: str) -> None:
    with jobs_lock:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = now_iso()
        jobs[job_id]["updated_at"] = now_iso()

    try:
        result = run_analysis(url, progress=lambda msg, lvl="info": add_log(job_id, msg, lvl), output_dir=OUTPUT_DIR)
        result = storage.save(result)
        with jobs_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["result"] = result
            jobs[job_id]["completed"] = 1
            jobs[job_id]["ended_at"] = now_iso()
            jobs[job_id]["updated_at"] = now_iso()
    except Exception as exc:
        add_log(job_id, f"Erro fatal: {exc}", "error")
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(exc)
            jobs[job_id]["ended_at"] = now_iso()
            jobs[job_id]["updated_at"] = now_iso()


def summarize_site_result(data: Dict[str, Any]) -> Dict[str, Any]:
    plugins = data.get("plugins", {})
    return {
        "url": data.get("url"),
        "status": "ok",
        "score_final": data.get("score_final", 0),
        "ranking": data.get("ranking"),
        "inicio": data.get("inicio"),
        "fim": data.get("fim"),
        "plugins_total": len(plugins),
        "plugins_ok": sum(1 for p in plugins.values() if p.get("status") == "ok"),
        "plugins_error": sum(1 for p in plugins.values() if p.get("status") == "error"),
        "arquivo_historico": data.get("arquivo_historico"),
    }


def aggregate_bulk_results(urls: List[str], site_results: List[Dict[str, Any]], settings: Dict[str, Any], started_at: str) -> Dict[str, Any]:
    scorer = Scorer()
    ok_items = [item for item in site_results if item.get("status") == "ok" and item.get("result")]
    error_items = [item for item in site_results if item.get("status") != "ok"]

    plugin_names = sorted({
        name
        for item in ok_items
        for name in (item.get("result") or {}).get("plugins", {}).keys()
    })
    plugins: Dict[str, Any] = {}

    for name in plugin_names:
        scores: List[float] = []
        weights: List[float] = []
        status_counts = {"ok": 0, "error": 0}
        per_site = []

        for item in ok_items:
            result = item.get("result") or {}
            plugin_data = (result.get("plugins") or {}).get(name)
            if not plugin_data:
                continue
            status = plugin_data.get("status", "ok")
            try:
                score = float(plugin_data.get("score", 0) or 0)
            except (TypeError, ValueError):
                score = 0.0
            try:
                weight = float(plugin_data.get("peso", 1) or 1)
            except (TypeError, ValueError):
                weight = 1.0
            scores.append(score)
            weights.append(weight)
            status_counts["ok" if status == "ok" else "error"] += 1
            per_site.append({
                "url": result.get("url") or item.get("url"),
                "status": status,
                "score": round(score, 2),
                "erro": plugin_data.get("erro"),
            })

        average = round(sum(scores) / len(scores), 2) if scores else 0
        plugins[name] = {
            "status": "ok" if status_counts["ok"] >= status_counts["error"] else "error",
            "score": average,
            "peso": round(sum(weights) / len(weights), 2) if weights else 1,
            "detalhes": {
                "sites_analisados": len(per_site),
                "media_score": average,
                "ok": status_counts["ok"],
                "erros": status_counts["error"],
                "por_site": per_site,
            },
        }

    score_values = [float((item.get("result") or {}).get("score_final", 0) or 0) for item in ok_items]
    avg_score = round(sum(score_values) / len(score_values), 2) if score_values else 0
    ranking = scorer.get_ranking(avg_score)
    ended_at = now_iso()

    result: Dict[str, Any] = {
        "mode": "bulk",
        "url": f"Bulk: {len(urls)} site(s)",
        "urls": urls,
        "inicio": started_at,
        "fim": ended_at,
        "plugins": plugins,
        "score_final": avg_score,
        "ranking": ranking,
        "bulk": {
            "label": f"Bulk: {len(urls)} site(s)",
            "total": len(urls),
            "ok": len(ok_items),
            "error": len(error_items),
            "delay_min": settings.get("min_delay"),
            "delay_max": settings.get("max_delay"),
            "score_medio": avg_score,
        },
        "results": [
            summarize_site_result(item.get("result") or {}) if item.get("status") == "ok" else {
                "url": item.get("url"),
                "status": "error",
                "erro": item.get("error"),
                "score_final": 0,
            }
            for item in site_results
        ],
    }
    return result


def save_bulk_result(result: Dict[str, Any]) -> Dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    latest_file = OUTPUT_DIR / "data.json"
    result["arquivo_resultado"] = str(latest_file.relative_to(BASE_DIR))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_file = HISTORY_DIR / f"{stamp}_bulk_{len(result.get('urls', []))}_sites.json"
    result["arquivo_historico"] = str(history_file.relative_to(BASE_DIR))

    latest_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    history_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def sleep_with_progress(job_id: str, seconds: float) -> None:
    remaining = int(round(seconds))
    while remaining > 0:
        time.sleep(min(1, remaining))
        remaining -= 1
        with jobs_lock:
            job = jobs.get(job_id)
            if job is not None:
                job["delay_remaining"] = remaining
                job["updated_at"] = now_iso()


def run_bulk_job(job_id: str, urls: List[str], settings: Dict[str, Any]) -> None:
    started_at = now_iso()
    with jobs_lock:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = started_at
        jobs[job_id]["updated_at"] = started_at

    site_results: List[Dict[str, Any]] = []
    total = len(urls)
    add_log(job_id, f"Modo bulk iniciado com {total} site(s).", "info")
    add_log(job_id, f"Pausa aleatória responsável: {settings['min_delay']}s a {settings['max_delay']}s entre sites.", "warning")

    for index, url in enumerate(urls, start=1):
        with jobs_lock:
            job = jobs.get(job_id)
            if job is not None:
                job["current_index"] = index
                job["current_url"] = url
                job["delay_remaining"] = 0
                job["updated_at"] = now_iso()

        add_log(job_id, f"[{index}/{total}] Analisando {url}", "info")
        try:
            result = run_analysis(url, progress=lambda msg, lvl="info": add_log(job_id, msg, lvl), output_dir=OUTPUT_DIR, save_history=False)
            site_results.append({"url": url, "status": "ok", "result": result})
            add_log(job_id, f"[{index}/{total}] Concluído: score {float(result.get('score_final', 0) or 0):.2f}", "success")
        except Exception as exc:
            site_results.append({"url": url, "status": "error", "error": str(exc)})
            add_log(job_id, f"[{index}/{total}] Erro em {url}: {exc}", "error")
            if settings.get("stop_on_error"):
                add_log(job_id, "Interrompido porque 'parar ao encontrar erro' está ativo.", "warning")
                break
        finally:
            with jobs_lock:
                job = jobs.get(job_id)
                if job is not None:
                    job["completed"] = len(site_results)
                    job["site_results"] = [
                        summarize_site_result(item.get("result") or {}) if item.get("status") == "ok" else {
                            "url": item.get("url"),
                            "status": "error",
                            "erro": item.get("error"),
                            "score_final": 0,
                        }
                        for item in site_results
                    ]
                    job["updated_at"] = now_iso()

        if index < total and not (settings.get("stop_on_error") and site_results[-1].get("status") == "error"):
            delay = random.uniform(float(settings["min_delay"]), float(settings["max_delay"]))
            add_log(job_id, f"Pausa de {delay:.1f}s antes do próximo site.", "warning")
            sleep_with_progress(job_id, delay)

    final_result = aggregate_bulk_results(urls, site_results, settings, started_at)
    final_result = save_bulk_result(final_result)
    final_result = storage.save(final_result)

    with jobs_lock:
        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = final_result
        jobs[job_id]["ended_at"] = now_iso()
        jobs[job_id]["updated_at"] = now_iso()
        jobs[job_id]["current_url"] = None
        jobs[job_id]["delay_remaining"] = 0
    add_log(job_id, f"Bulk concluído: {final_result['bulk']['ok']}/{final_result['bulk']['total']} site(s) OK. Média {final_result['score_final']:.2f}.", "success")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated") is True:
        return redirect(url_for("dashboard"))

    error = None
    next_url = request.values.get("next", "")

    if request.method == "POST":
        username = str(request.form.get("username", ""))
        password = str(request.form.get("password", ""))
        valid_user = hmac.compare_digest(username, ADMIN_USERNAME)
        valid_password = hmac.compare_digest(password, ADMIN_PASSWORD)

        if valid_user and valid_password:
            session.clear()
            session["authenticated"] = True
            session["username"] = ADMIN_USERNAME
            session.permanent = True
            destination = next_url if is_safe_next_url(next_url) else url_for("dashboard")
            return redirect(destination)

        error = "Usuário ou senha inválidos."

    return render_template("login.html", error=error, next_url=next_url), (401 if error else 200)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
def dashboard():
    return render_template("dashboard.html", current_user=session.get("username", ADMIN_USERNAME))


@app.get("/health")
def health():
    storage_health = storage.health()
    healthy = bool(storage_health.get("ok")) and not bool(storage_health.get("fallback_active"))
    status = "ok" if healthy else "degraded"
    return jsonify({
        "status": status,
        "port": int(os.getenv("PORT", "5840")),
        "app": "Colheiteira Dashboard",
        "storage": storage_health,
    }), (200 if healthy else 503)


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or request.form or {}
    raw_url = payload.get("url", "")

    try:
        url = normalize_url(raw_url)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    job_id = uuid.uuid4().hex[:12]
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "mode": "single",
            "url": url,
            "urls": [url],
            "status": "queued",
            "created_at": now_iso(),
            "started_at": None,
            "ended_at": None,
            "updated_at": now_iso(),
            "logs": [],
            "result": None,
            "error": None,
            "total": 1,
            "completed": 0,
            "current_index": 0,
            "current_url": None,
            "site_results": [],
        }

    thread = threading.Thread(target=run_job, args=(job_id, url), daemon=True)
    thread.start()
    return jsonify({"job_id": job_id, "status": "queued", "url": url, "mode": "single"})


@app.post("/api/bulk_analyze")
def bulk_analyze():
    payload = request.get_json(silent=True) or request.form or {}
    settings = bulk_settings_from_payload(payload)

    try:
        urls = parse_bulk_urls(payload.get("urls") or payload.get("url") or "", max_urls=settings["max_urls"])
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    job_id = uuid.uuid4().hex[:12]
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "mode": "bulk",
            "url": urls[0] if urls else None,
            "urls": urls,
            "settings": settings,
            "status": "queued",
            "created_at": now_iso(),
            "started_at": None,
            "ended_at": None,
            "updated_at": now_iso(),
            "logs": [],
            "result": None,
            "error": None,
            "total": len(urls),
            "completed": 0,
            "current_index": 0,
            "current_url": None,
            "delay_remaining": 0,
            "site_results": [],
        }

    thread = threading.Thread(target=run_bulk_job, args=(job_id, urls, settings), daemon=True)
    thread.start()
    return jsonify({"job_id": job_id, "status": "queued", "urls": urls, "mode": "bulk", "settings": settings})


@app.get("/api/jobs/<job_id>")
def get_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job não encontrado."}), 404
        return jsonify(job_public(job))


@app.get("/api/jobs")
def list_jobs():
    with jobs_lock:
        data = [job_public(job) for job in jobs.values()]
    data.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return jsonify(data[:30])


@app.get("/api/data")
def latest_data():
    try:
        latest = storage.latest()
        if not latest:
            return jsonify({"error": "Nenhuma análise encontrada ainda. Rode uma URL pelo dashboard."}), 404
        return jsonify(latest)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/history")
def history():
    try:
        return jsonify(storage.history(limit=80))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/result/<path:filename>")
def result_file(filename: str):
    try:
        result = storage.get(filename)
        if result is None:
            return jsonify({"error": "Resultado não encontrado."}), 404
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/plugins")
def plugins():
    config: Dict[str, Any] = {}
    if CONFIG_FILE.exists():
        try:
            config = read_json_file(CONFIG_FILE)
        except Exception:
            config = {}

    plugin_dirs = sorted(
        p.name for p in (BASE_DIR / "plugins").iterdir()
        if p.is_dir() and (p / "plugin.py").exists()
    )
    response = []
    for name in plugin_dirs:
        plugin_cfg = config.get(name, {})
        response.append({
            "name": name,
            "enabled": plugin_cfg.get("enabled", True),
            "weight": plugin_cfg.get("weight", 1),
            "config": plugin_cfg,
        })
    return jsonify(response)


@app.get("/api/settings")
def settings():
    return jsonify({"bulk": DEFAULT_BULK_SETTINGS, "port": int(os.getenv("PORT", "5840")), "storage": storage.health()})


@app.get("/api/diagnostics/lighthouse")
def diagnostics_lighthouse():
    return jsonify(lighthouse_diagnostic())


@app.post("/api/cache/clear")
def clear_cache():
    payload = request.get_json(silent=True) or {}
    include_history = bool(payload.get("include_history"))
    try:
        removed = storage.clear(include_history=include_history)
        return jsonify({"ok": True, "removed": removed, "storage": storage.name})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.get("/api/export/latest")
def export_latest():
    latest = storage.latest()
    if not latest:
        return jsonify({"error": "Nenhuma análise para exportar."}), 404

    if storage.name == "files":
        latest_file = OUTPUT_DIR / "data.json"
        if latest_file.exists():
            return send_file(latest_file, as_attachment=True, download_name="colheiteira_ultima_analise.json")

    from io import BytesIO

    payload = json.dumps(latest, ensure_ascii=False, indent=2).encode("utf-8")
    return send_file(
        BytesIO(payload),
        mimetype="application/json; charset=utf-8",
        as_attachment=True,
        download_name="colheiteira_ultima_analise.json",
    )


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 68)
    print("Colheiteira Dashboard iniciado")
    print("Acesse: http://localhost:5840")
    print("=" * 68 + "\n")
    port = int(os.getenv("PORT", "5840"))
    debug = os.getenv("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}
    app.run(debug=debug, host="0.0.0.0", port=port, threaded=True)
