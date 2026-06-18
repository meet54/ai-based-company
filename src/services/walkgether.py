"""In-house Walkgether project — requirements, progress, and deliverables."""

from datetime import datetime
from pathlib import Path

from src.config import settings
from src.database.state_store import app_state_store
from src.models.schemas import AgentRole, Project, ProjectStage, ProjectStatus
from src.services.walkgether_site import build_walkgether_site
from src.services.walkgether_app import build_walkgether_app_files

ROOT = Path(__file__).resolve().parent.parent.parent
REQUIREMENTS_FILE = ROOT / "walkgether.txt"
DELIVERABLES_DIR = ROOT / "deliverables" / "inhouse" / "walkgether"
WALKGETHER_STATE_KEY = "walkgether"
INHOUSE_ID = "walkgether"
INHOUSE_TITLE = "Walkgether"
INHOUSE_LABEL = "Walkgether (In-House)"

WALKGETHER_TASKS: list[dict] = [
    {
        "id": "mkt-brand",
        "role": AgentRole.MARKETING,
        "title": "Brand messaging & launch copy",
        "detail": "Crafting tagline, social posts, and app store descriptions for Walkgether.",
        "output": "Brand kit: 'Walk Together. Stay Healthy. Build Connections.' — hero copy, 5 social posts, App Store preview text.",
    },
    {
        "id": "sales-personas",
        "role": AgentRole.SALES,
        "title": "Target user personas",
        "detail": "Defining ideal walker segments: students, professionals, seniors, fitness enthusiasts.",
        "output": "4 personas documented with pain points, goals, and acquisition channels for each segment.",
    },
    {
        "id": "ba-requirements",
        "role": AgentRole.BUSINESS_ANALYST,
        "title": "MVP requirements document",
        "detail": "Formalizing MVP scope from walkgether.txt into user stories and acceptance criteria.",
        "output": "BRD with 8 MVP epics: auth, profiles, discovery, matching, groups, scheduling, messaging, safety.",
    },
    {
        "id": "hr-staffing",
        "role": AgentRole.HR,
        "title": "In-house team allocation",
        "detail": "Assigning sprint capacity for Walkgether alongside client project workload.",
        "output": "Sprint roster: 3 devs, 1 QA, 1 PM on Walkgether idle cycles; client work takes priority.",
    },
    {
        "id": "pm-sprint",
        "role": AgentRole.PROJECT_MANAGER,
        "title": "Sprint 1 planning",
        "detail": "Breaking MVP into 2-week sprints with milestones for landing page and core APIs.",
        "output": "Sprint 1 backlog: landing site, auth API spec, profile schema, discovery mock — 24 story points.",
    },
    {
        "id": "fe-landing",
        "role": AgentRole.FRONTEND_DEV,
        "title": "Walkgether landing page UI",
        "detail": "Building premium marketing site with hero, features, MVP scope, and waitlist form.",
        "output": "Landing page deployed: index.html, styles.css, app.js with responsive mobile-first design.",
        "builds_site": True,
    },
    {
        "id": "be-api",
        "role": AgentRole.BACKEND_DEV,
        "title": "Auth & profile API design",
        "detail": "Designing REST endpoints for registration, OTP, profiles, and nearby discovery.",
        "output": "OpenAPI spec: /auth/register, /auth/login, /profiles, /walkers/nearby — PostgreSQL schema draft.",
        "writes_doc": "docs/api-spec.md",
    },
    {
        "id": "fs-matching",
        "role": AgentRole.FULLSTACK_DEV,
        "title": "Walk matching algorithm spec",
        "detail": "Compatibility scoring: location, pace, schedule overlap, shared interests.",
        "output": "Matching engine spec with weighted scoring formula and Redis geo-index for proximity queries.",
        "writes_doc": "docs/matching-spec.md",
    },
    {
        "id": "qa-mvp",
        "role": AgentRole.QA_TESTER,
        "title": "MVP test plan",
        "detail": "Test cases for registration, discovery, matching, scheduling, and safety features.",
        "output": "42 test cases across 8 MVP modules — auth, profiles, map, match, schedule, chat, notify, safety.",
        "writes_doc": "docs/test-plan.md",
    },
    {
        "id": "fin-budget",
        "role": AgentRole.FINANCE,
        "title": "Internal project budget",
        "detail": "Tracking in-house development cost and projected launch runway for Walkgether.",
        "output": "Internal budget: $0 client revenue, infra est. $200/mo (maps, Firebase, hosting) at MVP scale.",
        "writes_doc": "docs/budget.md",
    },
    {
        "id": "cs-onboarding",
        "role": AgentRole.CLIENT_SUCCESS,
        "title": "User onboarding flow",
        "detail": "First-time user journey from signup to first scheduled walk.",
        "output": "5-step onboarding: welcome → profile → location → interests → first match suggestion.",
        "writes_doc": "docs/onboarding.md",
    },
    {
        "id": "fe-polish",
        "role": AgentRole.FRONTEND_DEV,
        "title": "Landing page polish & animations",
        "detail": "Refining Walkgether site UX — hover states, mobile nav, waitlist validation.",
        "output": "Polished landing: smooth scroll, mobile menu, waitlist form validation, accessibility pass.",
        "polish_site": True,
    },
]

WALKGETHER_APP_TASKS: list[dict] = [
    {
        "id": "hr-hire-mobile",
        "role": AgentRole.HR,
        "title": "Hire mobile app developers",
        "detail": "Recruiting React Native specialists for Walkgether iOS & Android MVP.",
        "output": "Hired mobile engineers: Manan Desai (Lead Mobile Dev) and Daxesh Bhoi (App Developer). Team expanded to 18.",
        "writes_doc": "docs/mobile-team-hiring.md",
    },
    {
        "id": "pm-app-kickoff",
        "role": AgentRole.PROJECT_MANAGER,
        "title": "Mobile app sprint kickoff",
        "detail": "Planning React Native MVP sprints: auth, discovery, matching, schedule, chat, profile.",
        "output": "App Sprint 1: project scaffold, navigation, auth + home screens — 32 story points over 3 weeks.",
        "writes_doc": "docs/app-sprint-plan.md",
    },
    {
        "id": "ba-app-stories",
        "role": AgentRole.BUSINESS_ANALYST,
        "title": "Mobile user stories",
        "detail": "Breaking MVP mobile features into sprint-ready user stories with acceptance criteria.",
        "output": "36 mobile user stories across 6 epics — auth, discover, match, schedule, chat, profile & safety.",
        "writes_doc": "docs/mobile-user-stories.md",
    },
    {
        "id": "mobile-scaffold",
        "role": AgentRole.MOBILE_DEV,
        "title": "React Native project scaffold",
        "detail": "Initializing Expo + React Navigation project structure for Walkgether.",
        "output": "Expo app created: App.tsx, package.json, tab navigator, theme tokens, folder structure.",
        "builds_app": True,
    },
    {
        "id": "mobile-auth",
        "role": AgentRole.MOBILE_DEV,
        "title": "Auth & onboarding screens",
        "detail": "Building login, signup, OTP, and 5-step onboarding flow screens.",
        "output": "AuthScreen + onboarding stack — email/phone/Google/Apple sign-in UI components.",
        "builds_app": True,
    },
    {
        "id": "app-discover",
        "role": AgentRole.APP_DEVELOPER,
        "title": "Discover & map screen",
        "detail": "Nearby walkers map with distance filters and location permissions.",
        "output": "DiscoverScreen with react-native-maps integration, geo filters, walker list cards.",
        "builds_app": True,
    },
    {
        "id": "mobile-matches",
        "role": AgentRole.MOBILE_DEV,
        "title": "Walk matching UI",
        "detail": "Compatibility scores, match cards, and schedule-walk CTA from matches.",
        "output": "MatchesScreen with weighted match scores, partner cards, quick-message actions.",
        "builds_app": True,
    },
    {
        "id": "app-schedule",
        "role": AgentRole.APP_DEVELOPER,
        "title": "Walk scheduling screen",
        "detail": "One-time and recurring walk events with calendar sync hooks.",
        "output": "ScheduleScreen — event list, create-walk FAB, recurring walk support stubs.",
        "builds_app": True,
    },
    {
        "id": "mobile-chat",
        "role": AgentRole.MOBILE_DEV,
        "title": "Messaging screen",
        "detail": "1:1 and group chat UI with Firebase Cloud Messaging integration plan.",
        "output": "ChatScreen — conversation list, unread badges, real-time message thread layout.",
        "builds_app": True,
    },
    {
        "id": "app-profile",
        "role": AgentRole.APP_DEVELOPER,
        "title": "Profile & safety settings",
        "detail": "User profile, pace/preferences, report & block, emergency contacts.",
        "output": "ProfileScreen — stats, edit profile, privacy settings, safety controls.",
        "builds_app": True,
    },
    {
        "id": "be-mobile-api",
        "role": AgentRole.BACKEND_DEV,
        "title": "Mobile API integration layer",
        "detail": "REST client setup, JWT auth flow, and mobile-specific API endpoints.",
        "output": "Mobile API client spec: auth tokens, /walkers/nearby, /matches, /walks, /messages.",
        "writes_doc": "docs/mobile-api-integration.md",
    },
    {
        "id": "qa-app-tests",
        "role": AgentRole.QA_TESTER,
        "title": "Mobile app test plan",
        "detail": "iOS/Android device testing matrix, screen flows, and regression checklist.",
        "output": "58 mobile test cases — auth flows, maps, matching, scheduling, chat, offline mode.",
        "writes_doc": "docs/mobile-test-plan.md",
    },
    {
        "id": "mobile-preview",
        "role": AgentRole.APP_DEVELOPER,
        "title": "Interactive app preview",
        "detail": "Building browser-based mobile preview with tab navigation for CEO demo.",
        "output": "Mobile preview live: 6-tab interactive prototype (Home, Discover, Matches, Schedule, Chat, Profile).",
        "builds_app_preview": True,
    },
]

APP_MAINTENANCE_TASKS: list[dict] = [
    {
        "id": "app-maint-review",
        "role": AgentRole.PROJECT_MANAGER,
        "title": "App build progress review",
        "detail": "Reviewing React Native MVP progress and App Store readiness.",
        "output": "App review: 6 core screens built, API integration in progress, TestFlight next.",
    },
    {
        "id": "app-maint-qa",
        "role": AgentRole.QA_TESTER,
        "title": "Mobile screen regression",
        "detail": "Testing all app screens on iOS and Android simulators.",
        "output": "All 6 tab screens pass navigation and layout checks on phone viewports.",
    },
]

MAINTENANCE_TASKS: list[dict] = [
    {
        "id": "maint-review",
        "role": AgentRole.PROJECT_MANAGER,
        "title": "Walkgether progress review",
        "detail": "Reviewing in-house build progress and prioritizing next improvements.",
        "output": "Sprint review complete — landing live, API specs ready, mobile app next phase.",
    },
    {
        "id": "maint-qa",
        "role": AgentRole.QA_TESTER,
        "title": "Landing page regression check",
        "detail": "Verifying Walkgether preview site across breakpoints and browsers.",
        "output": "Landing page passes responsive checks on mobile, tablet, and desktop viewports.",
    },
]


class WalkgetherService:
    def __init__(self) -> None:
        self._state: dict = {}
        self._requirements: str = ""

    def init(self) -> None:
        self._requirements = self._load_requirements()
        self._state = self._load_state()
        self._ensure_phase()
        self._ensure_deliverables()
        self._save_state()

    def _ensure_phase(self) -> None:
        if self._state.get("files_built") and self._state.get("phase") != "mobile_app":
            self._state["phase"] = "mobile_app"
        if "phase" not in self._state:
            self._state["phase"] = "website"
        if self._state.get("phase") == "mobile_app":
            self._state["hired_mobile_team"] = True

    def _load_requirements(self) -> str:
        if REQUIREMENTS_FILE.is_file():
            return REQUIREMENTS_FILE.read_text(encoding="utf-8")
        return "Walkgether — social fitness walking platform."

    def _default_state(self) -> dict:
        return {
            "completed_tasks": [],
            "task_cycle": 0,
            "files_built": False,
            "app_files_built": False,
            "phase": "website",
            "hired_mobile_team": False,
            "started_at": datetime.utcnow().isoformat(),
            "last_activity": None,
        }

    def _load_state(self) -> dict:
        stored = app_state_store.get(WALKGETHER_STATE_KEY)
        if stored:
            return stored
        return self._default_state()

    def _save_state(self) -> None:
        app_state_store.set(WALKGETHER_STATE_KEY, self._state)

    def _ensure_deliverables(self) -> None:
        if not self._state.get("files_built"):
            self._write_site_files()
            self._state["files_built"] = True
        if self._state.get("phase") == "mobile_app" and not self._state.get("app_files_built"):
            if (DELIVERABLES_DIR / "app" / "index.html").is_file():
                self._state["app_files_built"] = True
            else:
                self._write_mobile_files()

    def _write_site_files(self) -> None:
        DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
        for item in build_walkgether_site():
            dest = DELIVERABLES_DIR / item["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(item["content"], encoding="utf-8")

    def _write_doc(self, rel_path: str, content: str) -> None:
        dest = DELIVERABLES_DIR / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.is_file():
            dest.write_text(content, encoding="utf-8")

    def _write_mobile_files(self) -> None:
        from src.services.walkgether_app import build_walkgether_app_files
        DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
        for item in build_walkgether_app_files():
            if item["path"].startswith("app/"):
                continue
            dest = DELIVERABLES_DIR / item["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(item["content"], encoding="utf-8")
        self._state["app_files_built"] = True

    def _write_app_files(self) -> None:
        self._write_mobile_files()

    def _active_tasks(self) -> list[dict]:
        if self._state.get("phase") == "mobile_app":
            return WALKGETHER_APP_TASKS
        return WALKGETHER_TASKS

    def _active_maintenance(self) -> list[dict]:
        if self._state.get("phase") == "mobile_app":
            return APP_MAINTENANCE_TASKS
        return MAINTENANCE_TASKS

    def has_app_preview(self) -> bool:
        return (DELIVERABLES_DIR / "app" / "index.html").is_file()

    def app_preview_url(self) -> str | None:
        if self.has_app_preview():
            return "/walkgether/app"
        return None

    def as_project(self) -> Project:
        return Project(
            id=-1,
            title=INHOUSE_TITLE,
            client_company=settings.company_name,
            client_name="In-House Product",
            client_email=settings.ceo_email,
            description=(
                "Walkgether is our in-house social fitness platform. "
                "Phase 2: React Native mobile app for iOS & Android."
            ),
            requirements=self._requirements[:8000],
            tech_stack="React Native · Expo · Node.js/NestJS · PostgreSQL · Firebase · Google Maps",
            current_stage=ProjectStage.DEVELOPMENT,
            status=ProjectStatus.ACTIVE,
        )

    def has_preview(self) -> bool:
        return (DELIVERABLES_DIR / "index.html").is_file()

    def preview_url(self) -> str | None:
        if self.has_preview():
            return "/deliverables/inhouse/walkgether/index.html"
        return None

    def list_files(self) -> list[dict]:
        if not DELIVERABLES_DIR.exists():
            return []
        files = []
        for path in sorted(DELIVERABLES_DIR.rglob("*")):
            if path.is_file():
                rel = path.relative_to(DELIVERABLES_DIR).as_posix()
                files.append({
                    "path": rel,
                    "size": path.stat().st_size,
                    "extension": path.suffix.lstrip("."),
                })
        return files

    def read_file(self, file_path: str) -> str:
        base = DELIVERABLES_DIR.resolve()
        target = (base / file_path).resolve()
        if not str(target).startswith(str(base)):
            raise ValueError("Invalid file path")
        if not target.is_file():
            raise FileNotFoundError(file_path)
        return target.read_text(encoding="utf-8", errors="replace")

    def get_next_task(self, role: AgentRole) -> dict | None:
        completed = set(self._state.get("completed_tasks", []))
        tasks = self._active_tasks()
        for task in tasks:
            if task["role"] == role and task["id"] not in completed:
                return task
        cycle = self._state.get("task_cycle", 0)
        maint_list = self._active_maintenance()
        maint = maint_list[cycle % len(maint_list)]
        if maint["role"] == role:
            return maint
        for task in tasks:
            if task["role"] == role:
                return {**task, "id": f"{task['id']}-cycle-{cycle}", "repeat": True}
        return None

    def apply_task_result(self, task: dict) -> None:
        task_id = task["id"]
        if not task.get("repeat") and task_id not in self._state.get("completed_tasks", []):
            self._state.setdefault("completed_tasks", []).append(task_id)

        if task.get("builds_site"):
            self._write_site_files()
            self._state["files_built"] = True

        if task.get("polish_site"):
            self._write_site_files()

        if task.get("builds_app"):
            self._write_mobile_files()

        if task.get("builds_app_preview"):
            pass  # Live app served from deliverables/inhouse/walkgether/app/

        if task.get("id") == "hr-hire-mobile":
            self._state["hired_mobile_team"] = True

        doc_path = task.get("writes_doc")
        if doc_path:
            self._write_doc(doc_path, self._doc_content(task))

        self._state["last_activity"] = datetime.utcnow().isoformat()
        active = self._active_tasks()
        app_done = len([t for t in self._state.get("completed_tasks", []) if t in {x["id"] for x in active}])
        if app_done >= len(active):
            self._state["task_cycle"] = self._state.get("task_cycle", 0) + 1
        self._save_state()

    def _doc_content(self, task: dict) -> str:
        return f"""# {task['title']}

**Project:** Walkgether (In-House)  
**Company:** {settings.company_name}  
**Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

## Summary
{task['output']}

## Details
{task['detail']}

## Requirements Reference
See walkgether.txt for full product specification.
"""

    def get_status(self) -> dict:
        completed = self._state.get("completed_tasks", [])
        phase = self._state.get("phase", "website")
        active = self._active_tasks()
        active_ids = {t["id"] for t in active}
        done_count = len([t for t in completed if t in active_ids and not str(t).endswith("-cycle")])
        total = len(active)
        progress = min(100, round((done_count / total) * 100)) if total else 0
        mobile_team = [
            {"name": "Manan Desai", "role": "Lead Mobile Developer"},
            {"name": "Daxesh Bhoi", "role": "App Developer"},
        ]
        return {
            "id": INHOUSE_ID,
            "title": INHOUSE_TITLE,
            "label": INHOUSE_LABEL,
            "phase": phase,
            "phase_label": "Mobile App (React Native)" if phase == "mobile_app" else "Marketing Website",
            "tagline": "Walk Together. Stay Healthy. Build Connections.",
            "description": (
                "Building the Walkgether mobile app for iOS & Android. "
                "Idle team members work on this between client projects."
                if phase == "mobile_app"
                else "Social fitness platform — our in-house product."
            ),
            "progress_percent": progress,
            "tasks_completed": done_count,
            "tasks_total": total,
            "files_count": len(self.list_files()),
            "preview_available": self.has_preview(),
            "preview_url": self.preview_url(),
            "app_preview_available": self.has_app_preview(),
            "app_preview_url": self.app_preview_url(),
            "hired_mobile_team": self._state.get("hired_mobile_team", False),
            "mobile_team": mobile_team if self._state.get("hired_mobile_team") else [],
            "team_size": 13 if self._state.get("hired_mobile_team") else 11,
            "last_activity": self._state.get("last_activity"),
            "tech_stack": "React Native · Expo · Node.js · PostgreSQL · Firebase · Google Maps",
            "mvp_features": [
                "User registration & login",
                "Profile creation",
                "Nearby walker discovery",
                "Partner matching",
                "Walk scheduling",
                "1:1 messaging",
                "Push notifications",
                "Report & block",
            ],
        }


walkgether = WalkgetherService()
