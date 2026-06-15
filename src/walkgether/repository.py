import hashlib
import math
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.walkgether.models import (
    WalkgetherBase,
    WgBlock,
    WgMatch,
    WgMessage,
    WgNotification,
    WgReport,
    WgSession,
    WgUser,
    WgWalk,
)

wg_engine = create_async_engine(settings.database_url, echo=False)
wg_session_factory = async_sessionmaker(wg_engine, class_=AsyncSession, expire_on_commit=False)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371
    p = math.pi / 180
    a = (
        0.5
        - math.cos((lat2 - lat1) * p) / 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lng2 - lng1) * p)) / 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _user_dict(u: WgUser, distance_km: Optional[float] = None) -> dict:
    d = {
        "id": u.id,
        "name": u.name,
        "email": u.email if not u.is_demo else None,
        "bio": u.bio,
        "avatar": u.avatar,
        "pace": u.pace,
        "interests": u.interests,
        "availability": u.availability,
        "fitness_goal": u.fitness_goal,
        "lat": u.lat,
        "lng": u.lng,
        "is_demo": u.is_demo,
    }
    if distance_km is not None:
        d["distance_km"] = round(distance_km, 1)
    return d


def compatibility_score(me: WgUser, other: WgUser, distance_km: float) -> float:
    score = 50.0
    if me.pace == other.pace:
        score += 20
    elif me.pace in ("moderate", other.pace):
        score += 10
    if me.availability == other.availability:
        score += 15
    my_int = set(i.strip().lower() for i in me.interests.split(",") if i.strip())
    their_int = set(i.strip().lower() for i in other.interests.split(",") if i.strip())
    if my_int and their_int:
        overlap = len(my_int & their_int) / max(len(my_int | their_int), 1)
        score += overlap * 25
    if distance_km < 0.5:
        score += 15
    elif distance_km < 1.5:
        score += 8
    return min(99, round(score, 1))


class WalkgetherDB:
    async def init(self) -> None:
        async with wg_engine.begin() as conn:
            await conn.run_sync(WalkgetherBase.metadata.create_all)

    async def get_user(self, user_id: int) -> Optional[WgUser]:
        async with wg_session_factory() as session:
            return await session.get(WgUser, user_id)

    async def get_user_by_email(self, email: str) -> Optional[WgUser]:
        async with wg_session_factory() as session:
            result = await session.execute(select(WgUser).where(WgUser.email == email.lower()))
            return result.scalar_one_or_none()

    async def get_user_by_token(self, token: str) -> Optional[WgUser]:
        async with wg_session_factory() as session:
            result = await session.execute(select(WgSession).where(WgSession.token == token))
            sess = result.scalar_one_or_none()
            if not sess:
                return None
            return await session.get(WgUser, sess.user_id)

    async def register(self, email: str, password: str, name: str) -> tuple[WgUser, str]:
        email = email.lower().strip()
        async with wg_session_factory() as session:
            existing = await session.execute(select(WgUser).where(WgUser.email == email))
            if existing.scalar_one_or_none():
                raise ValueError("Email already registered")
            user = WgUser(
                email=email,
                password_hash=_hash_password(password),
                name=name.strip(),
                avatar="👤",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            token = secrets.token_urlsafe(32)
            session.add(WgSession(token=token, user_id=user.id))
            await session.commit()
            return user, token

    async def login(self, email: str, password: str) -> tuple[WgUser, str]:
        user = await self.get_user_by_email(email)
        if not user or user.password_hash != _hash_password(password):
            raise ValueError("Invalid email or password")
        token = secrets.token_urlsafe(32)
        async with wg_session_factory() as session:
            session.add(WgSession(token=token, user_id=user.id))
            await session.commit()
        return user, token

    async def update_profile(self, user_id: int, data: dict) -> WgUser:
        async with wg_session_factory() as session:
            user = await session.get(WgUser, user_id)
            if not user:
                raise ValueError("User not found")
            for key in ("name", "bio", "avatar", "pace", "interests", "availability", "fitness_goal", "lat", "lng"):
                if key in data and data[key] is not None:
                    setattr(user, key, data[key])
            await session.commit()
            await session.refresh(user)
            return user

    async def _blocked_ids(self, session: AsyncSession, user_id: int) -> set[int]:
        result = await session.execute(
            select(WgBlock).where(
                or_(WgBlock.blocker_id == user_id, WgBlock.blocked_id == user_id)
            )
        )
        ids: set[int] = set()
        for b in result.scalars().all():
            if b.blocker_id == user_id:
                ids.add(b.blocked_id)
            else:
                ids.add(b.blocker_id)
        return ids

    async def nearby_walkers(self, user_id: int, lat: float, lng: float, radius_km: float = 5.0) -> list[dict]:
        async with wg_session_factory() as session:
            me = await session.get(WgUser, user_id)
            blocked = await self._blocked_ids(session, user_id)
            result = await session.execute(select(WgUser).where(WgUser.id != user_id, WgUser.is_blocked == False))
            walkers = []
            for u in result.scalars().all():
                if u.id in blocked:
                    continue
                dist = _distance_km(lat, lng, u.lat, u.lng)
                if dist <= radius_km:
                    d = _user_dict(u, dist)
                    d["match_score"] = compatibility_score(me, u, dist)
                    walkers.append(d)
            walkers.sort(key=lambda x: x["match_score"], reverse=True)
            return walkers

    async def create_match(self, user_id: int, target_id: int) -> dict:
        async with wg_session_factory() as session:
            me = await session.get(WgUser, user_id)
            other = await session.get(WgUser, target_id)
            if not other:
                raise ValueError("User not found")
            dist = _distance_km(me.lat, me.lng, other.lat, other.lng)
            score = compatibility_score(me, other, dist)
            existing = await session.execute(
                select(WgMatch).where(
                    WgMatch.user_id == user_id,
                    WgMatch.matched_user_id == target_id,
                    WgMatch.status == "active",
                )
            )
            if existing.scalar_one_or_none():
                return {"status": "already_matched", "score": score}
            match = WgMatch(user_id=user_id, matched_user_id=target_id, score=score)
            session.add(match)
            session.add(
                WgNotification(
                    user_id=target_id,
                    title="New walking match!",
                    body=f"{me.name} wants to walk with you ({score}% compatible)",
                    ntype="match",
                )
            )
            await session.commit()
            return {"status": "matched", "score": score, "user": _user_dict(other, dist)}

    async def list_matches(self, user_id: int) -> list[dict]:
        async with wg_session_factory() as session:
            result = await session.execute(
                select(WgMatch).where(WgMatch.user_id == user_id, WgMatch.status == "active")
            )
            out = []
            for m in result.scalars().all():
                other = await session.get(WgUser, m.matched_user_id)
                if other:
                    out.append({"match_id": m.id, "score": m.score, "user": _user_dict(other)})
            return out

    async def schedule_walk(
        self, creator_id: int, title: str, location: str, scheduled_at: datetime, partner_id: Optional[int] = None
    ) -> dict:
        async with wg_session_factory() as session:
            walk = WgWalk(
                creator_id=creator_id,
                title=title,
                location=location,
                scheduled_at=scheduled_at,
                partner_id=partner_id,
            )
            session.add(walk)
            creator = await session.get(WgUser, creator_id)
            if partner_id:
                session.add(
                    WgNotification(
                        user_id=partner_id,
                        title="Walk scheduled",
                        body=f"{creator.name} invited you: {title} at {location}",
                        ntype="walk",
                    )
                )
            await session.commit()
            await session.refresh(walk)
            return {
                "id": walk.id,
                "title": walk.title,
                "location": walk.location,
                "scheduled_at": walk.scheduled_at.isoformat(),
                "partner_id": walk.partner_id,
                "status": walk.status,
            }

    async def list_walks(self, user_id: int) -> list[dict]:
        async with wg_session_factory() as session:
            result = await session.execute(
                select(WgWalk).where(
                    or_(WgWalk.creator_id == user_id, WgWalk.partner_id == user_id)
                ).order_by(WgWalk.scheduled_at)
            )
            return [
                {
                    "id": w.id,
                    "title": w.title,
                    "location": w.location,
                    "scheduled_at": w.scheduled_at.isoformat(),
                    "partner_id": w.partner_id,
                    "creator_id": w.creator_id,
                    "status": w.status,
                }
                for w in result.scalars().all()
            ]

    async def send_message(self, sender_id: int, receiver_id: int, body: str) -> dict:
        async with wg_session_factory() as session:
            msg = WgMessage(sender_id=sender_id, receiver_id=receiver_id, body=body.strip())
            session.add(msg)
            sender = await session.get(WgUser, sender_id)
            session.add(
                WgNotification(
                    user_id=receiver_id,
                    title=f"Message from {sender.name}",
                    body=body[:120],
                    ntype="message",
                )
            )
            await session.commit()
            await session.refresh(msg)
            return {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "body": msg.body,
                "created_at": msg.created_at.isoformat(),
            }

    async def get_messages(self, user_id: int, other_id: int, limit: int = 100) -> list[dict]:
        async with wg_session_factory() as session:
            result = await session.execute(
                select(WgMessage)
                .where(
                    or_(
                        and_(WgMessage.sender_id == user_id, WgMessage.receiver_id == other_id),
                        and_(WgMessage.sender_id == other_id, WgMessage.receiver_id == user_id),
                    )
                )
                .order_by(WgMessage.created_at)
                .limit(limit)
            )
            msgs = result.scalars().all()
            for m in msgs:
                if m.receiver_id == user_id and not m.read:
                    m.read = True
            await session.commit()
            return [
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "receiver_id": m.receiver_id,
                    "body": m.body,
                    "created_at": m.created_at.isoformat(),
                    "mine": m.sender_id == user_id,
                }
                for m in msgs
            ]

    async def list_conversations(self, user_id: int) -> list[dict]:
        async with wg_session_factory() as session:
            result = await session.execute(
                select(WgMessage).where(
                    or_(WgMessage.sender_id == user_id, WgMessage.receiver_id == user_id)
                ).order_by(WgMessage.created_at.desc())
            )
            seen: dict[int, dict] = {}
            for m in result.scalars().all():
                other_id = m.receiver_id if m.sender_id == user_id else m.sender_id
                if other_id not in seen:
                    other = await session.get(WgUser, other_id)
                    unread = await session.execute(
                        select(WgMessage).where(
                            WgMessage.sender_id == other_id,
                            WgMessage.receiver_id == user_id,
                            WgMessage.read == False,
                        )
                    )
                    seen[other_id] = {
                        "user": _user_dict(other) if other else {"id": other_id, "name": "Unknown"},
                        "last_message": m.body,
                        "last_at": m.created_at.isoformat(),
                        "unread": len(unread.scalars().all()),
                    }
            return list(seen.values())

    async def list_notifications(self, user_id: int) -> list[dict]:
        async with wg_session_factory() as session:
            result = await session.execute(
                select(WgNotification)
                .where(WgNotification.user_id == user_id)
                .order_by(WgNotification.created_at.desc())
                .limit(50)
            )
            notifs = result.scalars().all()
            for n in notifs:
                if not n.read:
                    n.read = True
            await session.commit()
            return [
                {
                    "id": n.id,
                    "title": n.title,
                    "body": n.body,
                    "type": n.ntype,
                    "created_at": n.created_at.isoformat(),
                }
                for n in notifs
            ]

    async def block_user(self, blocker_id: int, blocked_id: int) -> None:
        async with wg_session_factory() as session:
            session.add(WgBlock(blocker_id=blocker_id, blocked_id=blocked_id))
            await session.execute(
                select(WgMatch).where(
                    WgMatch.user_id == blocker_id,
                    WgMatch.matched_user_id == blocked_id,
                )
            )
            await session.commit()

    async def report_user(self, reporter_id: int, reported_id: int, reason: str) -> None:
        async with wg_session_factory() as session:
            session.add(WgReport(reporter_id=reporter_id, reported_id=reported_id, reason=reason))
            await session.commit()

    async def seed_demo_users(self) -> int:
        async with wg_session_factory() as session:
            result = await session.execute(select(WgUser).where(WgUser.is_demo == True))
            if result.scalars().first():
                return 0
            demos = [
                ("priya@walkgether.demo", "Priya Sharma", "👩", "moderate", "parks, morning walks, yoga", "morning", 23.025, 72.568),
                ("james@walkgether.demo", "James Wilson", "👨", "brisk", "trails, fitness, dogs", "evening", 23.018, 72.562),
                ("emma@walkgether.demo", "Emma Chen", "👩", "casual", "coffee walks, networking, city", "afternoon", 23.030, 72.575),
                ("tom@walkgether.demo", "Tom Lee", "👨", "moderate", "parks, photography, weekends", "morning", 23.015, 72.580),
                ("aisha@walkgether.demo", "Aisha Khan", "👩", "brisk", "fitness, lakeside, groups", "evening", 23.028, 72.555),
                ("marcus@walkgether.demo", "Marcus Johnson", "👨", "casual", "social walks, music, downtown", "afternoon", 23.020, 72.570),
                ("lisa@walkgether.demo", "Lisa Park", "👩", "moderate", "wellness, meditation walks", "morning", 23.032, 72.565),
                ("raj@walkgether.demo", "Raj Patel", "👨", "brisk", "marathon training, riverside", "evening", 23.012, 72.558),
            ]
            for email, name, avatar, pace, interests, avail, lat, lng in demos:
                session.add(
                    WgUser(
                        email=email,
                        password_hash=_hash_password("demo"),
                        name=name,
                        avatar=avatar,
                        pace=pace,
                        interests=interests,
                        availability=avail,
                        lat=lat,
                        lng=lng,
                        bio=f"Love walking around the city. Looking for {pace} pace partners.",
                        is_demo=True,
                    )
                )
            await session.commit()
            return len(demos)


walkgether_db = WalkgetherDB()
