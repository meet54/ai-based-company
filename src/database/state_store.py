"""Synchronous SQLite access for office, team live status, and JSON app state."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.database.models import AppStateDB, Base, OfficeAgentStateDB, TeamAgentLiveDB

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"

_sync_engine = create_engine(
    settings.database_url.replace("sqlite+aiosqlite:///", "sqlite:///"),
    echo=False,
)
SyncSession = sessionmaker(bind=_sync_engine, expire_on_commit=False)


def ensure_sync_tables() -> None:
    Base.metadata.create_all(bind=_sync_engine)


def _parse_dt(raw: str | datetime | None) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _team_row_to_dict(row: TeamAgentLiveDB) -> dict:
    return {
        "status": row.status,
        "role": row.role,
        "task": row.task,
        "details": row.details,
        "project_id": row.project_id,
        "project_title": row.project_title,
        "inhouse": row.inhouse,
        "office_activity": row.office_activity,
        "conversation_partner": row.conversation_partner,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


class OfficeStateStore:
    def load_all(self) -> dict[str, dict]:
        with SyncSession() as session:
            rows = session.scalars(select(OfficeAgentStateDB)).all()
            result: dict[str, dict] = {}
            for row in rows:
                entry: dict[str, Any] = {
                    "zone": row.zone,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
                if row.activity:
                    entry["activity"] = row.activity
                result[row.agent_name] = entry
            return result

    def get(self, agent_name: str) -> dict:
        with SyncSession() as session:
            row = session.get(OfficeAgentStateDB, agent_name)
            if not row:
                return {}
            entry: dict[str, Any] = {
                "zone": row.zone,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            if row.activity:
                entry["activity"] = row.activity
            return entry

    def upsert(self, agent_name: str, entry: dict) -> None:
        with SyncSession() as session:
            row = session.get(OfficeAgentStateDB, agent_name)
            if not row:
                row = OfficeAgentStateDB(agent_name=agent_name)
            row.zone = entry.get("zone", "desk")
            row.activity = entry.get("activity")
            row.updated_at = datetime.utcnow()
            session.add(row)
            session.commit()

    def save_all(self, agents: dict[str, dict]) -> None:
        with SyncSession() as session:
            for name, entry in agents.items():
                row = session.get(OfficeAgentStateDB, name)
                if not row:
                    row = OfficeAgentStateDB(agent_name=name)
                row.zone = entry.get("zone", "desk")
                row.activity = entry.get("activity")
                row.updated_at = _parse_dt(entry.get("updated_at")) or datetime.utcnow()
                session.add(row)
            session.commit()

    def count(self) -> int:
        with SyncSession() as session:
            return session.scalar(select(func.count()).select_from(OfficeAgentStateDB)) or 0


class TeamLiveStore:
    def get(self, agent_name: str) -> Optional[dict]:
        with SyncSession() as session:
            row = session.get(TeamAgentLiveDB, agent_name)
            return _team_row_to_dict(row) if row else None

    def load_all(self) -> dict[str, dict]:
        with SyncSession() as session:
            rows = session.scalars(select(TeamAgentLiveDB)).all()
            return {row.agent_name: _team_row_to_dict(row) for row in rows}

    def upsert(self, agent_name: str, data: dict) -> None:
        with SyncSession() as session:
            row = session.get(TeamAgentLiveDB, agent_name)
            if not row:
                row = TeamAgentLiveDB(agent_name=agent_name)
            row.status = data.get("status", "idle")
            row.role = data.get("role", "")
            row.task = data.get("task", "")
            row.details = data.get("details", "")
            row.project_id = data.get("project_id")
            row.project_title = data.get("project_title")
            row.inhouse = bool(data.get("inhouse", False))
            row.office_activity = data.get("office_activity")
            row.conversation_partner = data.get("conversation_partner")
            row.started_at = _parse_dt(data.get("started_at"))
            row.updated_at = datetime.utcnow()
            session.add(row)
            session.commit()


class AppStateStore:
    def get(self, key: str, default: dict | None = None) -> dict:
        with SyncSession() as session:
            row = session.get(AppStateDB, key)
            if row and isinstance(row.value, dict):
                return row.value
            return default if default is not None else {}

    def set(self, key: str, value: dict) -> None:
        with SyncSession() as session:
            row = session.get(AppStateDB, key)
            if not row:
                row = AppStateDB(key=key, value=value)
            else:
                row.value = value
            row.updated_at = datetime.utcnow()
            session.add(row)
            session.commit()

    def has(self, key: str) -> bool:
        with SyncSession() as session:
            return session.get(AppStateDB, key) is not None


office_store = OfficeStateStore()
team_live_store = TeamLiveStore()
app_state_store = AppStateStore()


def migrate_json_to_database() -> None:
    """One-time import from data/*.json into SQLite (skipped if DB already populated)."""
    ensure_sync_tables()

    if office_store.count() == 0:
        path = DATA_DIR / "office_state.json"
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                agents = raw.get("agents", raw) if isinstance(raw, dict) else {}
                if isinstance(agents, dict) and agents:
                    office_store.save_all(agents)
            except (json.JSONDecodeError, OSError):
                pass

    if not app_state_store.has("walkgether"):
        path = DATA_DIR / "walkgether_state.json"
        if path.is_file():
            try:
                app_state_store.set("walkgether", json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass

    if not app_state_store.has("discovered_leads"):
        path = DATA_DIR / "discovered_leads.json"
        if path.is_file():
            try:
                app_state_store.set("discovered_leads", json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass


ensure_sync_tables()
migrate_json_to_database()
