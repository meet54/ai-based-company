"""Drives coffee breaks, calls, gaming, and teammate Q&A in the virtual office."""

import asyncio
import random

from src.agents.team import TEAM_ROSTER, get_social_team, is_social_team_member
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

SOCIAL_TEAM_NAMES = frozenset(m.name for m in get_social_team())

CALL_TARGETS = [
    "client stakeholder",
    "vendor partner",
    "Walkgether beta user",
    "sales prospect",
    "QA lead",
]

SOCIAL_CALL_TARGETS = [
    "client brand manager",
    "Instagram support",
    "ad platform rep",
    "influencer partner",
    "content approval contact",
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

SOCIAL_QUERY_TEMPLATES = [
    "Can you review the reel hook for {topic} before we publish?",
    "Does the {topic} ad copy match the brand voice for {project}?",
    "What's our posting cadence for {topic} this week?",
    "Should we boost the {topic} post or wait for organic reach?",
    "Can you align the carousel visuals with the {topic} campaign?",
    "Any client feedback on the {topic} creatives so far?",
    "Who is approving the {topic} assets for {project}?",
    "Should we A/B test headlines for the {topic} ad set?",
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

SOCIAL_QUERY_TOPICS = [
    "Instagram reels",
    "LinkedIn carousel",
    "paid ad creatives",
    "brand hashtag set",
    "content calendar",
    "reel thumbnails",
    "story templates",
    "engagement report",
    "influencer brief",
    "client approval pack",
]

ANSWER_TEMPLATES = [
    "Good question — I'd use {approach} for {topic}. Let's sync after standup.",
    "Yes, we covered that in the last sprint. I'll share the doc in Slack.",
    "Not yet — I'm finishing {topic} first, should be ready by EOD.",
    "I'd recommend we keep it simple for MVP and iterate on {topic} next sprint.",
    "I checked with the team — we're aligned on {approach} for {project}.",
]

SOCIAL_ANSWER_TEMPLATES = [
    "Looks good — I'd tighten the CTA on {topic} and ship after client sign-off.",
    "Yes, the {topic} visuals match our palette. I'll queue them in the calendar.",
    "Let's hold the {topic} boost until we get Nayani's final review.",
    "I'll update the {topic} copy and share the preview in the social channel.",
    "Client liked the direction — we can publish {topic} for {project} tomorrow.",
]

SOCIAL_DESK_TASKS = [
    "Reviewing reel thumbnails",
    "Scheduling posts for next week",
    "Polishing ad copy variants",
    "Updating the content calendar",
    "Preparing client approval pack",
    "Checking engagement metrics",
    "Drafting carousel captions",
    "Aligning brand templates",
]


def _first_name(name: str) -> str:
    return (name or "").split()[0]


def _project_for(member_name: str) -> str:
    live = team_monitor.get_agent_status(member_name) or {}
    return live.get("project_title") or "Walkgether"


def _generate_query(asker: str, responder: str, *, social: bool) -> tuple[str, str]:
    project = _project_for(asker)
    if social:
        topic = random.choice(SOCIAL_QUERY_TOPICS)
        query = random.choice(SOCIAL_QUERY_TEMPLATES).format(project=project, topic=topic)
        answer = random.choice(SOCIAL_ANSWER_TEMPLATES).format(
            topic=topic,
            project=project,
        )
        return query, answer

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

    def _idle_members(self, *, social: bool | None = None) -> list:
        members = []
        for member in TEAM_ROSTER:
            if member.role == AgentRole.CEO:
                continue
            if social is True and not is_social_team_member(member.name):
                continue
            if social is False and is_social_team_member(member.name):
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

        social_idle = self._idle_members(social=True)
        dev_idle = self._idle_members(social=False)

        if social_idle and (not dev_idle or random.random() < 0.42):
            await self._tick_social(social_idle)
        elif dev_idle:
            await self._tick_dev(dev_idle)

    async def _tick_social(self, idle: list) -> None:
        roll = random.random()
        if roll < 0.38:
            await self._start_social_desk_work(random.choice(idle))
        elif roll < 0.52:
            await self._start_coffee(random.choice(idle))
        elif roll < 0.68:
            await self._start_phone(random.choice(idle), social=True)
        elif roll < 0.8:
            await self._start_gaming(random.choice(idle))
        elif len(idle) >= 2:
            asker, responder = random.sample(idle, 2)
            await self._start_query(asker, responder, zone="social_floor", social=True)

    async def _tick_dev(self, idle: list) -> None:
        roll = random.random()
        if roll < 0.24:
            await self._start_coffee(random.choice(idle))
        elif roll < 0.44:
            await self._start_phone(random.choice(idle))
        elif roll < 0.6:
            await self._start_gaming(random.choice(idle))
        elif len(idle) >= 2:
            asker, responder = random.sample(idle, 2)
            await self._start_query(asker, responder, zone="meeting_room", social=False)

    async def _start_social_desk_work(self, member) -> None:
        task = random.choice(SOCIAL_DESK_TASKS)
        office_state.set_zone(member.name, "social_floor")
        team_monitor.set_idle(
            member.name,
            member.role.value,
            task,
            "Working from the Social Media department.",
        )
        await db.log_activity(
            ActivityLog(
                project_id=None,
                agent_role=member.role,
                agent_name=member.name,
                action=task,
                details="At desk in the Social Media department.",
                stage=None,
            )
        )

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

    async def _start_phone(self, member, *, social: bool = False) -> None:
        targets = SOCIAL_CALL_TARGETS if social else CALL_TARGETS
        target = random.choice(targets)
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

    async def _start_query(
        self,
        asker,
        responder,
        *,
        zone: str,
        social: bool,
    ) -> None:
        query, answer = _generate_query(asker.name, responder.name, social=social)
        office_state.start_query_pair(
            asker.name,
            responder.name,
            query,
            answer,
            QUERY_DURATION_SEC,
            zone=zone,
        )

        responder_first = _first_name(responder.name)
        location = (
            "the Social Media department"
            if social
            else "the meeting room"
        )

        team_monitor.set_social_activity(
            asker.name,
            asker.role.value,
            f"Asking {responder_first}: {query[:80]}",
            f"Discussing with {responder.name} in {location}.",
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
