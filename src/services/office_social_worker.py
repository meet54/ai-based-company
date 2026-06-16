"""Drives coffee breaks, calls, gaming, and teammate Q&A in the virtual office."""

import asyncio
import random

from src.agents.team import TEAM_ROSTER
from src.database.repository import db
from src.models.schemas import ActivityLog, AgentRole
from src.services.office_hours import is_office_open
from src.services.office_state import office_state
from src.services.team_monitor import team_monitor
from src.services.workflow_lock import workflow_lock

POLL_INTERVAL_SEC = 10
COFFEE_DURATION_SEC = 150
PHONE_DURATION_SEC = 180
GAMING_DURATION_SEC = 200
QUERY_DURATION_SEC = 120

CALL_TARGETS = [
    "client stakeholder",
    "vendor partner",
    "Walkgether beta user",
    "sales prospect",
    "QA lead",
]

GAMES = [
    "table tennis",
    "FIFA",
    "chess",
    "Mario Kart",
    "pool",
]

QUERY_TEMPLATES = [
    "Can you clarify the API contract for {project}?",
    "Do we have test coverage for the {topic} flow yet?",
    "What's blocking the {topic} work this sprint?",
    "Should we use WebSockets or polling for {topic}?",
    "Can you review my approach to {topic}?",
    "Is the {topic} spec finalized for handoff?",
    "Any concerns with the timeline for {project}?",
    "Who owns the {topic} integration on your side?",
]

QUERY_TOPICS = [
    "mobile auth",
    "push notifications",
    "walk matching",
    "profile API",
    "landing page",
    "QA regression",
    "sprint planning",
    "deployment pipeline",
    "user onboarding",
    "payment flow",
]

ANSWER_TEMPLATES = [
    "Good question — I'd use {approach} for {topic}. Let's sync after standup.",
    "Yes, we covered that in the last sprint. I'll share the doc in Slack.",
    "Not yet — I'm finishing {topic} first, should be ready by EOD.",
    "I'd recommend we keep it simple for MVP and iterate on {topic} next sprint.",
    "I checked with the team — we're aligned on {approach} for {project}.",
]


def _first_name(name: str) -> str:
    return (name or "").split()[0]


def _project_for(member_name: str) -> str:
    live = team_monitor.get_agent_status(member_name) or {}
    return live.get("project_title") or "Walkgether"


def _generate_query(asker: str, responder: str) -> tuple[str, str]:
    project = _project_for(asker)
    topic = random.choice(QUERY_TOPICS)
    query = random.choice(QUERY_TEMPLATES).format(project=project, topic=topic)
    approach = random.choice(["a REST endpoint", "Redis caching", "feature flags", "the shared module"])
    answer = random.choice(ANSWER_TEMPLATES).format(
        approach=approach,
        topic=topic,
        project=project,
    )
    return query, answer


class OfficeSocialWorker:
    def __init__(self) -> None:
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
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

    def _idle_members(self) -> list:
        members = []
        for member in TEAM_ROSTER:
            if member.role == AgentRole.CEO:
                continue
            live = team_monitor.get_agent_status(member.name)
            if live and live.get("status") == "working":
                continue
            if office_state.get_activity(member.name):
                continue
            members.append(member)
        return members

    async def _tick(self) -> None:
        if not is_office_open():
            return
        if workflow_lock.is_busy():
            return

        office_state.clear_expired()

        idle = self._idle_members()
        if len(idle) < 1:
            return

        roll = random.random()
        if roll < 0.22:
            await self._start_coffee(random.choice(idle))
        elif roll < 0.42:
            await self._start_phone(random.choice(idle))
        elif roll < 0.58:
            await self._start_gaming(random.choice(idle))
        elif roll < 0.78 and len(idle) >= 2:
            asker, responder = random.sample(idle, 2)
            await self._start_query(asker, responder)

    async def _start_coffee(self, member) -> None:
        office_state.start_coffee_break(member.name, COFFEE_DURATION_SEC)
        team_monitor.set_social_activity(
            member.name,
            member.role.value,
            "Coffee break",
            "Relaxing in the coffee break room.",
            office_activity="coffee",
        )
        await db.log_activity(
            ActivityLog(
                project_id=None,
                agent_role=member.role,
                agent_name=member.name,
                action="Coffee break",
                details="In the coffee break room.",
                stage=None,
            )
        )

    async def _start_phone(self, member) -> None:
        target = random.choice(CALL_TARGETS)
        office_state.start_phone_call(member.name, target, PHONE_DURATION_SEC)
        team_monitor.set_social_activity(
            member.name,
            member.role.value,
            f"Call with {target}",
            "In the call room on a phone meeting.",
            office_activity="phone",
            partner=target.title(),
        )
        await db.log_activity(
            ActivityLog(
                project_id=None,
                agent_role=member.role,
                agent_name=member.name,
                action="Phone call",
                details=f"Call room — speaking with {target}.",
                stage=None,
            )
        )

    async def _start_gaming(self, member) -> None:
        game = random.choice(GAMES)
        office_state.start_gaming(member.name, game, GAMING_DURATION_SEC)
        team_monitor.set_social_activity(
            member.name,
            member.role.value,
            f"Playing {game}",
            "Chilling in the games room.",
            office_activity="gaming",
        )
        await db.log_activity(
            ActivityLog(
                project_id=None,
                agent_role=member.role,
                agent_name=member.name,
                action=f"Games room — {game}",
                details=f"Relaxing with {game} in the chill room.",
                stage=None,
            )
        )

    async def _start_query(self, asker, responder) -> None:
        query, answer = _generate_query(asker.name, responder.name)
        office_state.start_query_pair(
            asker.name,
            responder.name,
            query,
            answer,
            QUERY_DURATION_SEC,
        )

        responder_first = _first_name(responder.name)

        team_monitor.set_social_activity(
            asker.name,
            asker.role.value,
            f"Asking {responder_first}: {query[:80]}",
            f"Discussing with {responder.name} at their desk.",
            office_activity="query",
            partner=responder.name,
        )
        team_monitor.set_social_activity(
            responder.name,
            responder.role.value,
            f"Answering {_first_name(asker.name)}'s question",
            answer[:200],
            office_activity="query",
            partner=asker.name,
        )

        await db.log_activity(
            ActivityLog(
                project_id=None,
                agent_role=asker.role,
                agent_name=asker.name,
                action=f"Asked {responder.name}",
                details=query,
                stage=None,
            )
        )
        await db.log_activity(
            ActivityLog(
                project_id=None,
                agent_role=responder.role,
                agent_name=responder.name,
                action=f"Answered {_first_name(asker.name)}",
                details=answer[:300],
                stage=None,
            )
        )


office_social_worker = OfficeSocialWorker()
