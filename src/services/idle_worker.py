"""Assigns idle AI team members to the in-house Walkgether project."""

import asyncio
import random

from src.agents.team import TEAM_ROSTER
from src.database.repository import db
from src.models.schemas import ActivityLog, AgentRole
from src.services.team_monitor import team_monitor
from src.services.walkgether import INHOUSE_LABEL, walkgether
from src.services.workflow_lock import workflow_lock

POLL_INTERVAL_SEC = 8
WORK_DURATION_SEC = 5


class IdleWorker:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False
        self._agent_index = 0
        self._busy_agents: set[str] = set()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        walkgether.init()
        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception:
                pass
            await asyncio.sleep(POLL_INTERVAL_SEC)

    def stop(self) -> None:
        self._running = False

    async def _tick(self) -> None:
        if workflow_lock.is_busy():
            return

        member = self._next_idle_member()
        if not member:
            return

        task = walkgether.get_next_task(member.role)
        if not task:
            return

        self._busy_agents.add(member.name)
        team_monitor.set_working_inhouse(
            member.name,
            member.role.value,
            task["title"],
            task["detail"],
        )

        await asyncio.sleep(WORK_DURATION_SEC)

        if workflow_lock.is_busy():
            team_monitor.set_idle(
                member.name,
                member.role.value,
                "Paused — client project in progress",
                "Walkgether work resumed when available.",
            )
            self._busy_agents.discard(member.name)
            return

        walkgether.apply_task_result(task)

        await db.log_activity(
            ActivityLog(
                project_id=None,
                agent_role=member.role,
                agent_name=member.name,
                action=f"Walkgether: {task['title']}",
                details=task["output"],
                stage=None,
            )
        )

        team_monitor.set_idle_on_inhouse(
            member.name,
            member.role.value,
            f"Walkgether — {task['title']}",
            task["output"][:200],
        )
        self._busy_agents.discard(member.name)

    def _next_idle_member(self):
        roster = list(TEAM_ROSTER)
        random.shuffle(roster)
        for _ in range(len(roster)):
            member = roster[self._agent_index % len(roster)]
            self._agent_index += 1
            if member.name in self._busy_agents:
                continue
            live = team_monitor.get_agent_status(member.name)
            if live and live.get("status") == "working":
                continue
            if member.role == AgentRole.CEO:
                continue
            return member
        return None


idle_worker = IdleWorker()
