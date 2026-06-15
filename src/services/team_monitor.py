from datetime import datetime
from typing import Optional

from src.agents.team import TEAM_ROSTER
from src.models.schemas import Project

INHOUSE_PROJECT_TITLE = "Walkgether (In-House)"


class TeamMonitor:
    """Tracks what each AI team member is doing right now (CCTV-style)."""

    def __init__(self):
        self._agents: dict[str, dict] = {}

    def set_working(
        self,
        agent_name: str,
        role: str,
        project: Optional[Project],
        task: str,
        details: str = "",
    ) -> None:
        self._agents[agent_name] = {
            "status": "working",
            "role": role,
            "task": task,
            "details": details,
            "project_id": project.id if project else None,
            "project_title": project.title if project else None,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def set_working_inhouse(
        self,
        agent_name: str,
        role: str,
        task: str,
        details: str = "",
    ) -> None:
        self._agents[agent_name] = {
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

    def set_idle_on_inhouse(
        self, agent_name: str, role: str, last_action: str, details: str = ""
    ) -> None:
        self._agents[agent_name] = {
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

    def set_idle(self, agent_name: str, role: str, last_action: str, details: str = "") -> None:
        prev = self._agents.get(agent_name, {})
        self._agents[agent_name] = {
            "status": "idle",
            "role": role,
            "task": last_action,
            "details": details,
            "project_id": prev.get("project_id"),
            "project_title": prev.get("project_title"),
            "started_at": prev.get("started_at"),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def get_agent_status(self, agent_name: str) -> Optional[dict]:
        return self._agents.get(agent_name)

    def build_live_roster(self, activity_by_agent: dict[str, dict]) -> list[dict]:
        roster = []
        working_count = 0
        for member in TEAM_ROSTER:
            live = self._agents.get(member.name, {})
            log = activity_by_agent.get(member.name)
            status = live.get("status", "idle")
            if status == "working":
                working_count += 1
            elif log and not live:
                status = "idle"

            roster.append({
                "id": member.id,
                "name": member.name,
                "role": member.role.value,
                "department": member.department,
                "skills": member.skills,
                "status": status,
                "current_task": live.get("task") or (log.get("action") if log else "Standing by"),
                "work_details": live.get("details") or (log.get("details", "")[:300] if log else "Ready for next assignment"),
                "project_id": live.get("project_id") or (log.get("project_id") if log else None),
                "project_title": live.get("project_title") or (log.get("project_title") if log else None),
                "inhouse": live.get("inhouse", False),
                "last_active": live.get("updated_at") or (log.get("created_at") if log else None),
                "stage": log.get("stage") if log else None,
            })
        return roster, working_count


team_monitor = TeamMonitor()
