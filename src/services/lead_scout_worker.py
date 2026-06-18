"""Background worker — scans free platforms for new client leads."""

import asyncio

from src.agents.team import get_member_by_role
from src.database.repository import db
from src.models.schemas import ActivityLog, AgentRole
from src.services.lead_scout import lead_scout
from src.services.team_monitor import team_monitor
from src.services.workflow_lock import workflow_lock
from src.config import settings


class LeadScoutWorker:
    def __init__(self) -> None:
        self._running = False

    async def start(self) -> None:
        if not settings.lead_scout_enabled:
            return
        self._running = True
        await asyncio.sleep(5)
        while self._running:
            try:
                if not workflow_lock.is_busy():
                    await self._scan_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                pass
            await asyncio.sleep(settings.lead_scan_interval_sec)

    def stop(self) -> None:
        self._running = False

    async def _scan_cycle(self) -> None:
        marketing = get_member_by_role(AgentRole.MARKETING)
        sales = get_member_by_role(AgentRole.SALES)

        team_monitor.set_working_inhouse(
            marketing.name,
            marketing.role.value,
            "Scanning USA, UK, EU, India & Japan gigs",
            "Freelance only — Germany excluded…",
        )
        team_monitor.set_working_inhouse(
            sales.name,
            sales.role.value,
            "Qualifying regional freelance leads",
            "Reviewing r/forhire, IndiaBusiness, LondonJobs…",
        )
        result = await lead_scout.scan()
        new_count = result.get("new_count", 0)
        detail = result.get("message", "Scan complete")
        await db.log_activity(
            ActivityLog(
                project_id=None,
                agent_role=AgentRole.MARKETING,
                agent_name=marketing.name,
                action="Lead scan completed",
                details=detail,
                stage=None,
            )
        )
        team_monitor.set_idle(
            marketing.name,
            marketing.role.value,
            "Lead discovery",
            f"{detail}. {new_count} new prospect(s)." if new_count else detail,
        )
        team_monitor.set_idle(
            sales.name,
            sales.role.value,
            "Lead qualification",
            "Ready to approach prospects from live feed.",
        )


lead_scout_worker = LeadScoutWorker()
