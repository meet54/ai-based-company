"""Persists each team member's virtual office location and social activity in SQLite."""

from datetime import datetime, timedelta

from src.database.state_store import office_store

VALID_ZONES = frozenset({
    "desk", "coffee", "coffee_room", "lounge", "hallway", "entrance", "away",
    "phone_room", "chill_room",
})
IDLE_BREAK_ZONES = ("coffee_room", "phone_room", "chill_room", "lounge", "hallway")
ACTIVITY_COFFEE = "coffee_break"
ACTIVITY_QUERY = "query"
ACTIVITY_PHONE = "phone_call"
ACTIVITY_GAMING = "gaming"

ZONE_ALIASES = {"coffee": "coffee_room"}


class OfficeState:
    def __init__(self) -> None:
        raw = office_store.load_all()
        self._zones: dict[str, dict] = {}
        for name, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            zone = ZONE_ALIASES.get(entry.get("zone", "desk"), entry.get("zone", "desk"))
            if zone in VALID_ZONES:
                self._zones[name] = {**entry, "zone": zone}

    def _load(self) -> dict[str, dict]:
        return office_store.load_all()

    def _save(self) -> None:
        office_store.save_all(self._zones)

    def _save_agent(self, agent_name: str) -> None:
        entry = self._zones.get(agent_name, {})
        office_store.upsert(agent_name, entry)

    def _utcnow(self) -> datetime:
        return datetime.utcnow()

    def _parse_until(self, activity: dict) -> datetime | None:
        raw = activity.get("until")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None

    def get_entry(self, agent_name: str) -> dict:
        return self._zones.get(agent_name, {})

    def get_zone(self, agent_name: str) -> str:
        zone = self._zones.get(agent_name, {}).get("zone", "desk")
        return ZONE_ALIASES.get(zone, zone)

    def get_activity(self, agent_name: str) -> dict | None:
        activity = self._zones.get(agent_name, {}).get("activity")
        if not activity:
            return None
        until = self._parse_until(activity)
        if until and until <= self._utcnow():
            return None
        return activity

    def _zone_for_activity(self, activity: dict) -> str:
        t = activity.get("type")
        if t == ACTIVITY_COFFEE:
            return "coffee_room"
        if t == ACTIVITY_QUERY:
            return "desk"
        if t == ACTIVITY_PHONE:
            return "phone_room"
        if t == ACTIVITY_GAMING:
            return "chill_room"
        return "desk"

    def resolve_zone(self, agent_name: str, status: str) -> str:
        if status == "working":
            return "desk"
        activity = self.get_activity(agent_name)
        if activity:
            return self._zone_for_activity(activity)
        if agent_name in self._zones:
            zone = self.get_zone(agent_name)
            if zone in IDLE_BREAK_ZONES and not activity:
                return "desk"
            return zone
        return "desk"

    def ensure_zone(self, agent_name: str, status: str) -> str:
        return self.resolve_zone(agent_name, status)

    def set_zone(self, agent_name: str, zone: str) -> None:
        zone = ZONE_ALIASES.get(zone, zone)
        if zone not in VALID_ZONES:
            zone = "desk"
        prev = self._zones.get(agent_name, {}).get("zone")
        if prev == zone and not self._zones.get(agent_name, {}).get("activity"):
            return
        entry = self._zones.get(agent_name, {})
        entry["zone"] = zone
        entry["updated_at"] = self._utcnow().isoformat()
        self._zones[agent_name] = entry
        self._save_agent(agent_name)

    def start_coffee_break(self, agent_name: str, duration_sec: int = 150) -> None:
        until = (self._utcnow() + timedelta(seconds=duration_sec)).isoformat()
        self._zones[agent_name] = {
            "zone": "coffee_room",
            "activity": {"type": ACTIVITY_COFFEE, "until": until},
            "updated_at": self._utcnow().isoformat(),
        }
        self._save_agent(agent_name)

    def start_phone_call(self, agent_name: str, call_with: str, duration_sec: int = 180) -> None:
        until = (self._utcnow() + timedelta(seconds=duration_sec)).isoformat()
        self._zones[agent_name] = {
            "zone": "phone_room",
            "activity": {
                "type": ACTIVITY_PHONE,
                "partner": call_with,
                "until": until,
            },
            "updated_at": self._utcnow().isoformat(),
        }
        self._save_agent(agent_name)

    def start_gaming(self, agent_name: str, game: str, duration_sec: int = 200) -> None:
        until = (self._utcnow() + timedelta(seconds=duration_sec)).isoformat()
        self._zones[agent_name] = {
            "zone": "chill_room",
            "activity": {
                "type": ACTIVITY_GAMING,
                "game": game,
                "until": until,
            },
            "updated_at": self._utcnow().isoformat(),
        }
        self._save_agent(agent_name)

    def start_query_pair(
        self,
        asker: str,
        responder: str,
        query: str,
        answer: str,
        duration_sec: int = 120,
    ) -> None:
        until = (self._utcnow() + timedelta(seconds=duration_sec)).isoformat()
        now = self._utcnow().isoformat()
        self._zones[asker] = {
            "zone": "desk",
            "activity": {
                "type": ACTIVITY_QUERY,
                "role": "asker",
                "partner": responder,
                "query": query,
                "answer": answer,
                "until": until,
            },
            "updated_at": now,
        }
        self._zones[responder] = {
            "zone": "desk",
            "activity": {
                "type": ACTIVITY_QUERY,
                "role": "responder",
                "partner": asker,
                "query": query,
                "answer": answer,
                "until": until,
            },
            "updated_at": now,
        }
        self._save_agent(asker)
        self._save_agent(responder)

    def clear_activity(self, agent_name: str, zone: str = "desk") -> None:
        entry = self._zones.get(agent_name, {})
        entry.pop("activity", None)
        entry["zone"] = zone
        entry["updated_at"] = self._utcnow().isoformat()
        self._zones[agent_name] = entry
        self._save_agent(agent_name)

    def clear_expired(self) -> list[str]:
        expired: list[str] = []
        for name, entry in list(self._zones.items()):
            activity = entry.get("activity")
            if not activity:
                continue
            until = self._parse_until(activity)
            if until and until <= self._utcnow():
                expired.append(name)
                self.clear_activity(name, zone="desk")
        return expired

    def on_working(self, agent_name: str) -> None:
        entry = self._zones.get(agent_name, {})
        entry.pop("activity", None)
        entry["zone"] = "desk"
        entry["updated_at"] = self._utcnow().isoformat()
        self._zones[agent_name] = entry
        self._save_agent(agent_name)

    def on_idle(self, agent_name: str) -> None:
        if self.get_activity(agent_name):
            return
        self.set_zone(agent_name, "desk")

    def on_absent(self, agent_name: str) -> None:
        self.clear_activity(agent_name, zone="away")

    def activity_display(self, agent_name: str) -> dict:
        activity = self.get_activity(agent_name)
        if not activity:
            return {
                "office_activity": "idle",
                "office_zone": self.resolve_zone(agent_name, "idle"),
                "conversation_partner": None,
                "office_query": None,
                "office_answer": None,
            }

        zone = self._zone_for_activity(activity)
        partner = activity.get("partner")
        query = activity.get("query")
        answer = activity.get("answer")
        role = activity.get("role")

        if activity["type"] == ACTIVITY_COFFEE:
            return {
                "office_activity": "coffee",
                "office_zone": zone,
                "conversation_partner": None,
                "office_query": None,
                "office_answer": None,
                "current_task": "Coffee break",
                "work_details": "Relaxing in the coffee break room.",
            }

        if activity["type"] == ACTIVITY_PHONE:
            who = partner or "client"
            return {
                "office_activity": "phone",
                "office_zone": zone,
                "conversation_partner": partner,
                "office_query": None,
                "office_answer": None,
                "current_task": f"On a call with {who.split()[0]}",
                "work_details": f"In the call room — speaking with {who}.",
            }

        if activity["type"] == ACTIVITY_GAMING:
            game = activity.get("game", "games")
            return {
                "office_activity": "gaming",
                "office_zone": zone,
                "conversation_partner": None,
                "office_query": None,
                "office_answer": None,
                "current_task": f"Playing {game}",
                "work_details": "Chilling in the games room.",
            }

        first = (partner or "").split()[0] if partner else "teammate"
        if role == "asker":
            task = f"Asking {first}: {query[:70]}{'…' if query and len(query) > 70 else ''}"
            details = f"Waiting for {partner}'s answer at their desk."
        else:
            task = f"Answering {first}'s question"
            details = answer or f"Helping {partner} with a quick question at their desk."

        return {
            "office_activity": "query",
            "office_zone": zone,
            "conversation_partner": partner,
            "office_query": query,
            "office_answer": answer,
            "current_task": task,
            "work_details": details,
        }


office_state = OfficeState()
