"""Persistência híbrida para resultados do Colheiteira.

- Sem DATABASE_URL: mantém o comportamento original baseado em JSON local.
- Com DATABASE_URL: usa PostgreSQL/Supabase via SQLAlchemy.

A API exposta por :class:`ResultStorage` é deliberadamente pequena para que o
motor de análise continue independente do provedor de banco.
"""
from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, List, Optional

# SQLAlchemy é opcional no modo local. Assim, uma instalação antiga continua
# abrindo o dashboard em arquivos mesmo antes de atualizar as dependências.
SQLALCHEMY_IMPORT_ERROR: Optional[Exception] = None
try:
    from sqlalchemy import (
        JSON,
        Column,
        DateTime,
        Float,
        MetaData,
        String,
        Table,
        Text,
        create_engine,
        delete,
        insert,
        select,
        update,
    )
    from sqlalchemy.engine import Engine
    from sqlalchemy.pool import NullPool
except ImportError as exc:  # pragma: no cover - exercitado em instalações antigas
    SQLALCHEMY_IMPORT_ERROR = exc


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "sim"}


def _normalize_database_url(url: str) -> str:
    """Converte URLs copiadas do Supabase para o driver psycopg 3."""
    value = (url or "").strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://") :]
    if value.startswith("postgresql://"):
        value = "postgresql+psycopg://" + value[len("postgresql://") :]
    return value


def _filename_from_path(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    # Resultados antigos foram gerados no Windows e podem conter barras invertidas.
    return Path(PureWindowsPath(raw).name).name


def _safe_domain(url: str) -> str:
    domain = re.sub(r"^https?://", "", url or "", flags=re.I).split("/")[0]
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", domain).strip("_") or "resultado"


def _generated_filename(result: Dict[str, Any]) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if result.get("mode") == "bulk":
        return f"{stamp}_bulk_{len(result.get('urls') or [])}_sites.json"
    return f"{stamp}_{_safe_domain(str(result.get('url') or 'resultado'))}.json"


def summarize_result(result: Dict[str, Any], filename: str, modified_at: Optional[str] = None) -> Dict[str, Any]:
    plugins = result.get("plugins") or {}
    bulk = result.get("bulk") or {}
    return {
        "file": filename,
        "path": result.get("arquivo_historico") or result.get("arquivo_resultado") or filename,
        "storage_id": result.get("storage_id"),
        "mode": result.get("mode", "single"),
        "url": result.get("url") or bulk.get("label"),
        "score_final": result.get("score_final"),
        "ranking": result.get("ranking"),
        "inicio": result.get("inicio"),
        "fim": result.get("fim"),
        "plugins_total": len(plugins),
        "plugins_ok": sum(1 for item in plugins.values() if item.get("status") == "ok"),
        "plugins_error": sum(1 for item in plugins.values() if item.get("status") == "error"),
        "sites_total": bulk.get("total"),
        "sites_ok": bulk.get("ok"),
        "sites_error": bulk.get("error"),
        "modified_at": modified_at or result.get("fim") or result.get("inicio"),
    }


class FileResultBackend:
    name = "files"

    def __init__(self, base_dir: Path, output_dir: Path):
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.history_dir = output_dir / "history"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def save(self, result: Dict[str, Any], filename: Optional[str] = None) -> Dict[str, Any]:
        # O analyzer já salva os arquivos. Este método garante compatibilidade
        # quando um resultado vier de outro fluxo ou de uma futura fila externa.
        latest = self.output_dir / "data.json"
        resolved_name = filename or _filename_from_path(result.get("arquivo_historico")) or _generated_filename(result)
        history = self.history_dir / Path(resolved_name).name

        result.setdefault("arquivo_resultado", str(latest.relative_to(self.base_dir)))
        result.setdefault("arquivo_historico", str(history.relative_to(self.base_dir)))
        result["storage_backend"] = self.name

        payload = json.dumps(result, ensure_ascii=False, indent=2)
        latest.write_text(payload, encoding="utf-8")
        if not history.exists() or history.read_text(encoding="utf-8") != payload:
            history.write_text(payload, encoding="utf-8")
        return result

    def latest(self) -> Optional[Dict[str, Any]]:
        path = self.output_dir / "data.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def history(self, limit: int = 80) -> List[Dict[str, Any]]:
        self.history_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(self.history_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        items: List[Dict[str, Any]] = []
        for path in files[:limit]:
            try:
                result = json.loads(path.read_text(encoding="utf-8"))
                items.append(summarize_result(
                    result,
                    path.name,
                    datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                ))
            except Exception as exc:
                items.append({
                    "file": path.name,
                    "path": str(path.relative_to(self.base_dir)),
                    "error": str(exc),
                    "modified_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                })
        return items

    def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        safe_name = Path(PureWindowsPath(identifier).name).name
        for path in (self.history_dir / safe_name, self.output_dir / safe_name):
            if path.exists() and path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
        return None

    def clear(self, include_history: bool = False) -> List[str]:
        removed: List[str] = []
        latest = self.output_dir / "data.json"
        if latest.exists():
            latest.unlink()
            removed.append(str(latest.relative_to(self.base_dir)))
        if include_history:
            for path in self.history_dir.glob("*.json"):
                path.unlink()
                removed.append(str(path.relative_to(self.base_dir)))
        return removed

    def health(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "backend": self.name,
            "persistent": False,
            "output_dir": str(self.output_dir),
        }


class DatabaseResultBackend:
    name = "database"

    def __init__(self, database_url: str):
        if SQLALCHEMY_IMPORT_ERROR is not None:
            raise RuntimeError(
                "SQLAlchemy/psycopg não estão instalados. Rode novamente setup.bat ou scripts/setup.sh."
            ) from SQLALCHEMY_IMPORT_ERROR
        self.database_url = _normalize_database_url(database_url)
        self.metadata = MetaData()
        self.results = Table(
            "colheiteira_analysis_results",
            self.metadata,
            Column("id", String(36), primary_key=True),
            Column("filename", String(255), unique=True, nullable=False, index=True),
            Column("mode", String(20), nullable=False, default="single", index=True),
            Column("url", Text, nullable=True),
            Column("score_final", Float, nullable=True),
            Column("ranking", String(120), nullable=True),
            Column("started_at", String(64), nullable=True),
            Column("finished_at", String(64), nullable=True),
            Column("result_data", JSON, nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow, index=True),
            Column("updated_at", DateTime(timezone=True), nullable=False, default=utcnow),
        )
        self.state = Table(
            "colheiteira_app_state",
            self.metadata,
            Column("key", String(100), primary_key=True),
            Column("value", Text, nullable=True),
            Column("updated_at", DateTime(timezone=True), nullable=False, default=utcnow),
        )
        self.engine = self._create_engine()
        self.metadata.create_all(self.engine)
        self._lock = threading.RLock()

    def _create_engine(self) -> Engine:
        kwargs: Dict[str, Any] = {"pool_pre_ping": True}
        lower_url = self.database_url.lower()
        # Supavisor em transaction mode (porta 6543) não aceita prepared statements.
        is_postgres = lower_url.startswith(("postgresql://", "postgresql+psycopg://", "postgres://"))
        transaction_pooler = is_postgres and ":6543/" in lower_url
        if transaction_pooler or _env_bool("DB_USE_NULL_POOL", False):
            kwargs["poolclass"] = NullPool
            if is_postgres:
                kwargs["connect_args"] = {"prepare_threshold": None}
        return create_engine(self.database_url, **kwargs)

    def _set_state(self, conn: Any, key: str, value: Optional[str]) -> None:
        existing = conn.execute(select(self.state.c.key).where(self.state.c.key == key)).first()
        values = {"value": value, "updated_at": utcnow()}
        if existing:
            conn.execute(update(self.state).where(self.state.c.key == key).values(**values))
        else:
            conn.execute(insert(self.state).values(key=key, **values))

    def _get_state(self, conn: Any, key: str) -> Optional[str]:
        row = conn.execute(select(self.state.c.value).where(self.state.c.key == key)).first()
        return row[0] if row else None

    def save(self, result: Dict[str, Any], filename: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            resolved_name = filename or _filename_from_path(result.get("arquivo_historico")) or _generated_filename(result)
            record_id = str(result.get("storage_id") or uuid.uuid4())
            result["storage_id"] = record_id
            result["storage_backend"] = self.name
            result["storage_filename"] = resolved_name
            payload = json.loads(json.dumps(result, ensure_ascii=False, default=str))
            values = {
                "id": record_id,
                "filename": resolved_name,
                "mode": str(result.get("mode") or "single"),
                "url": str(result.get("url") or "") or None,
                "score_final": float(result.get("score_final")) if result.get("score_final") is not None else None,
                "ranking": str(result.get("ranking") or "") or None,
                "started_at": str(result.get("inicio") or "") or None,
                "finished_at": str(result.get("fim") or "") or None,
                "result_data": payload,
                "updated_at": utcnow(),
            }
            with self.engine.begin() as conn:
                existing = conn.execute(
                    select(self.results.c.id).where(self.results.c.filename == resolved_name)
                ).first()
                if existing:
                    record_id = existing[0]
                    result["storage_id"] = record_id
                    payload["storage_id"] = record_id
                    values["id"] = record_id
                    values["result_data"] = payload
                    conn.execute(
                        update(self.results).where(self.results.c.id == record_id).values(**values)
                    )
                else:
                    values["created_at"] = utcnow()
                    conn.execute(insert(self.results).values(**values))
                self._set_state(conn, "latest_result_id", record_id)
            return result

    def latest(self) -> Optional[Dict[str, Any]]:
        with self.engine.connect() as conn:
            latest_id = self._get_state(conn, "latest_result_id")
            if not latest_id:
                return None
            row = conn.execute(
                select(self.results.c.result_data).where(self.results.c.id == latest_id)
            ).first()
            return dict(row[0]) if row else None

    def history(self, limit: int = 80) -> List[Dict[str, Any]]:
        stmt = (
            select(self.results.c.filename, self.results.c.result_data, self.results.c.updated_at)
            .order_by(self.results.c.created_at.desc())
            .limit(max(1, min(int(limit), 500)))
        )
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).all()
        return [
            summarize_result(
                dict(row.result_data),
                row.filename,
                row.updated_at.isoformat() if row.updated_at else None,
            )
            for row in rows
        ]

    def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        safe_name = Path(PureWindowsPath(identifier).name).name
        stmt = select(self.results.c.result_data).where(
            (self.results.c.id == identifier) | (self.results.c.filename == safe_name)
        )
        with self.engine.connect() as conn:
            row = conn.execute(stmt).first()
        return dict(row[0]) if row else None

    def clear(self, include_history: bool = False) -> List[str]:
        removed: List[str] = []
        with self.engine.begin() as conn:
            latest_id = self._get_state(conn, "latest_result_id")
            if latest_id:
                removed.append(f"database:latest:{latest_id}")
            self._set_state(conn, "latest_result_id", None)
            if include_history:
                count = conn.execute(select(self.results.c.id)).all()
                conn.execute(delete(self.results))
                removed.extend(f"database:history:{row[0]}" for row in count)
        return removed

    def health(self) -> Dict[str, Any]:
        try:
            with self.engine.connect() as conn:
                conn.execute(select(1)).scalar_one()
            return {"ok": True, "backend": self.name, "persistent": True}
        except Exception as exc:
            return {"ok": False, "backend": self.name, "persistent": True, "error": str(exc)}


class ResultStorage:
    """Facade com fallback seguro para preservar o modo local."""

    def __init__(self, base_dir: Path, output_dir: Path):
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.requested_backend = os.getenv("STORAGE_BACKEND", "auto").strip().lower()
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.strict = _env_bool("STORAGE_STRICT", bool(os.getenv("RAILWAY_ENVIRONMENT")))
        self.initialization_error: Optional[str] = None

        use_database = self.requested_backend in {"database", "postgres", "postgresql", "supabase"} or (
            self.requested_backend == "auto" and bool(self.database_url)
        )

        if use_database:
            if not self.database_url:
                message = "STORAGE_BACKEND pede banco, mas DATABASE_URL não foi definida."
                if self.strict:
                    raise RuntimeError(message)
                self.initialization_error = message
                self.backend: Any = FileResultBackend(base_dir, output_dir)
            else:
                try:
                    self.backend = DatabaseResultBackend(self.database_url)
                except Exception as exc:
                    message = f"Falha ao inicializar o banco: {exc}"
                    if self.strict:
                        raise RuntimeError(message) from exc
                    self.initialization_error = message
                    self.backend = FileResultBackend(base_dir, output_dir)
        else:
            self.backend = FileResultBackend(base_dir, output_dir)

    @property
    def name(self) -> str:
        return self.backend.name

    def save(self, result: Dict[str, Any], filename: Optional[str] = None) -> Dict[str, Any]:
        return self.backend.save(result, filename)

    def latest(self) -> Optional[Dict[str, Any]]:
        return self.backend.latest()

    def history(self, limit: int = 80) -> List[Dict[str, Any]]:
        return self.backend.history(limit)

    def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        return self.backend.get(identifier)

    def clear(self, include_history: bool = False) -> List[str]:
        return self.backend.clear(include_history)

    def health(self) -> Dict[str, Any]:
        data = self.backend.health()
        data.update({
            "requested_backend": self.requested_backend,
            "fallback_active": bool(self.initialization_error),
        })
        if self.initialization_error:
            data["initialization_error"] = self.initialization_error
        return data


__all__ = ["ResultStorage", "summarize_result"]
