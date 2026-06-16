from datetime import datetime
from typing import Optional

from src.agents.team import TEAM_ROSTER
from src.database.state_store import team_live_store
from src.models.schemas import Project
from src.services.office_hours import closed_status_message, is_office_open
from src.services.office_state import office_state

INHOUSE_PROJECT_TITLE = "Walkgether (In-House)"


class TeamMonitor:
    """Tracks what each AI team member is doing right now (persisted in SQLite)."""

    def _persist(self, agent_name: str, data: dict) -> None:
        team_live_store.upsert(agent_name, data)

    def set_working(
        self,
        agent_name: str,
        role: str,
        project: Optional[Project],
        task: str,
        details: str = "",
    ) -> None:
        data = {
            "status": "working",
            "role": role,
            "task": task,
            "details": details,
            "project_id": project.id if project else None,
            "project_title": project.title if project else None,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._persist(agent_name, data)
        office_state.on_working(agent_name)

    def set_working_inhouse(
        self,
        agent_name: str,
        role: str,
        task: str,
        details: str = "",
    ) -> None:
        data = {
            "status": "working",
            "role": role,
            "task": task,
            "details": details,
            "project_id": None,
            "project_title": INHOUSE_PROJECT_TITLE,
            "inhouse": True,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._persist(agent_name, data)
        office_state.on_working(agent_name)

    def set_idle_on_inhouse(
        self, agent_name: str, role: str, last_action: str, details: str = ""
    ) -> None:
        data = {
            "status": "idle",
            "role": role,
            "task": last_action,
            "details": details,
            "project_id": None,
            "project_title": INHOUSE_PROJECT_TITLE,
            "inhouse": True,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._persist(agent_name, data)
        office_state.on_idle(agent_name)

    def set_idle(self, agent_name: str, role: str, last_action: str, details: str = "") -> None:
        prev = team_live_store.get(agent_name) or {}
        data = {
            "status": "idle",
            "role": role,
            "task": last_action,
            "details": details,
            "project_id": prev.get("project_id"),
            "project_title": prev.get("project_title"),
            "started_at": prev.get("started_at"),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._persist(agent_name, data)
        office_state.on_idle(agent_name)

    def set_social_activity(
        self,
        agent_name: str,
        role: str,
        task: str,
        details: str = "",
        office_activity: str = "idle",
        partner: str | None = None,
    ) -> None:
        prev = team_live_store.get(agent_name) or {}
        data = {
            "status": "idle",
            "role": role,
            "task": task,
            "details": details,
            "project_id": prev.get("project_id"),
            "project_title": prev.get("project_title"),
            "inhouse": prev.get("inhouse", False),
            "office_activity": office_activity,
            "conversation_partner": partner,
            "started_at": prev.get("started_at"),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._persist(agent_name, data)

    def get_agent_status(self, agent_name: str) -> Optional[dict]:
        return team_live_store.get(agent_name)

    def _build_closed_roster(self) -> list[dict]:
        live_by_name = team_live_store.load_all()
        message = closed_status_message()
        roster = []
        for member in TEAM_ROSTER:
            live = live_by_name.get(member.name, {})
            roster.append({
                "id": member.id,
                "name": member.name,
                "role": member.role.value,
                "department": member.department,
                "skills": member.skills,
                "status": "away",
                "current_task": "Logged out",
                "work_details": message,
                "project_id": None,
                "project_title": None,
                "inhouse": False,
                "last_active": live.get("updated_at"),
                "stage": None,
                "office_zone": "away",
                "office_activity": "offline",
                "office_game": None,
                "conversation_partner": None,
                "office_query": None,
                "office_answer": None,
            })
        return roster

    def build_live_roster(self, activity_by_agent: dict[str, dict]) -> list[dict]:
        if not is_office_open():
            return self._build_closed_roster(), 0

        live_by_name = team_live_store.load_all()
        roster = []
        working_count = 0
        for member in TEAM_ROSTER:
            live = live_by_name.get(member.name, {})
            log = activity_by_agent.get(member.name)
            status = live.get("status", "idle")
            if status == "working":
                working_count += 1
            elif log and not live:
                status = "idle"

            activity_info = office_state.activity_display(member.name)
            office_zone = office_state.resolve_zone(member.name, status)
            current_task = live.get("task") or (log.get("action") if log else "Standing by")
            work_details = live.get("details") or (
                log.get("details", "")[:300] if log else "Ready for next assignment"
            )

            social = activity_info.get("office_activity")
            if social and social != "idle":
                current_task = activity_info.get("current_task", current_task)
                work_details = activity_info.get("work_details", work_details)
                office_zone = office_state.resolve_zone(member.name, status)

            roster.append({
                "id": member.id,
                "name": member.name,
                "role": member.role.value,
                "department": member.department,
                "skills": member.skills,
                "status": status,
                "current_task": current_task,
                "work_details": work_details,
                "project_id": live.get("project_id") or (log.get("project_id") if log else None),
                "project_title": live.get("project_title") or (log.get("project_title") if log else None),
                "inhouse": live.get("inhouse", False),
                "last_active": live.get("updated_at") or (log.get("created_at") if log else None),
                "stage": log.get("stage") if log else None,
                "office_zone": office_zone,
                "office_activity": activity_info.get("office_activity", "idle"),
                "office_game": activity_info.get("office_game"),
                "conversation_partner": activity_info.get("conversation_partner"),
                "office_query": activity_info.get("office_query"),
                "office_answer": activity_info.get("office_answer"),
            })
        return roster, working_count


team_monitor = TeamMonitor()
