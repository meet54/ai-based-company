from src.models.schemas import AgentRole, TeamMember

TEAM_ROSTER: list[TeamMember] = [
    TeamMember(
        id="ceo-001",
        name="Meet Suthar",
        role=AgentRole.CEO,
        department="Executive",
        skills=["strategy", "final approval", "business direction", "client relationships"],
    ),
    TeamMember(
        id="sales-001",
        name="Pritesh Parmar",
        role=AgentRole.SALES,
        department="Sales",
        skills=["lead generation", "client negotiation", "requirement discovery", "CRM"],
    ),
    TeamMember(
        id="mkt-001",
        name="Ayushi Rami",
        role=AgentRole.MARKETING,
        department="Marketing",
        skills=["digital marketing", "SEO", "content strategy", "brand awareness"],
    ),
    TeamMember(
        id="hr-001",
        name="Monali Pahurkar",
        role=AgentRole.HR,
        department="Human Resources",
        skills=["recruitment", "team coordination", "onboarding", "performance tracking"],
    ),
    TeamMember(
        id="ba-001",
        name="Dhruv Shukhadia",
        role=AgentRole.BUSINESS_ANALYST,
        department="Business Analysis",
        skills=["requirements analysis", "user stories", "process mapping", "documentation"],
    ),
    TeamMember(
        id="fin-001",
        name="Dhruv Shukhadia",
        role=AgentRole.FINANCE,
        department="Finance",
        skills=["quotation", "invoicing", "payment tracking", "budget estimation"],
    ),
    TeamMember(
        id="pm-001",
        name="Manan Patel",
        role=AgentRole.PROJECT_MANAGER,
        department="Project Management",
        skills=["sprint planning", "code review", "quality oversight", "client communication"],
    ),
    TeamMember(
        id="qa-001",
        name="Manan Patel",
        role=AgentRole.QA_TESTER,
        department="Quality Assurance",
        skills=["manual testing", "automated testing", "bug reporting", "regression testing"],
    ),
    TeamMember(
        id="be-001",
        name="Manan Desai",
        role=AgentRole.BACKEND_DEV,
        department="Engineering",
        skills=["Python", "Node.js", "APIs", "databases", "microservices"],
    ),
    TeamMember(
        id="fs-001",
        name="Manan Desai",
        role=AgentRole.FULLSTACK_DEV,
        department="Engineering",
        skills=["full-stack development", "React", "Python", "deployment", "architecture"],
    ),
    TeamMember(
        id="fe-001",
        name="Daxesh Bhoi",
        role=AgentRole.FRONTEND_DEV,
        department="Engineering",
        skills=["React", "Vue", "HTML/CSS", "responsive design", "UI implementation"],
    ),
    TeamMember(
        id="cs-001",
        name="Daxesh Bhoi",
        role=AgentRole.CLIENT_SUCCESS,
        department="Client Success",
        skills=["handover documentation", "training", "support", "feedback collection"],
    ),
    # Social media team
    TeamMember(
        id="smtl-001",
        name="Nayani Gour",
        role=AgentRole.SOCIAL_TEAM_LEADER,
        department="Social Media",
        skills=["campaign strategy", "team leadership", "client reviews", "brand voice"],
    ),
    TeamMember(
        id="sme-001",
        name="Nittal Gamit",
        role=AgentRole.SOCIAL_MEDIA_EXECUTIVE,
        department="Social Media",
        skills=["post scheduling", "ad copy", "community management", "platform publishing"],
    ),
    TeamMember(
        id="sma-001",
        name="Jatin Panchal",
        role=AgentRole.SOCIAL_MEDIA_ANALYST,
        department="Social Media",
        skills=["analytics", "audience research", "content calendar", "performance reporting"],
    ),
    TeamMember(
        id="smc-001",
        name="Rutvi Parmar",
        role=AgentRole.SOCIAL_MEDIA_COORDINATOR,
        department="Social Media",
        skills=["content coordination", "campaign scheduling", "cross-platform publishing", "client comms"],
    ),
    TeamMember(
        id="gd-001",
        name="Harshil Pathak",
        role=AgentRole.GRAPHIC_DESIGNER,
        department="Creative",
        skills=["visual design", "ad creatives", "reel thumbnails", "brand assets"],
    ),
    TeamMember(
        id="gd-002",
        name="Margie Shah",
        role=AgentRole.GRAPHIC_DESIGNER_2,
        department="Creative",
        skills=["visual design", "ad creatives", "social templates", "brand identity"],
    ),
]


def get_member_by_role(role: AgentRole) -> TeamMember:
    for member in TEAM_ROSTER:
        if member.role == role:
            return member
    raise ValueError(f"No team member found for role: {role}")


def get_member_by_id(member_id: str) -> TeamMember | None:
    for member in TEAM_ROSTER:
        if member.id == member_id:
            return member
    return None


def get_members_by_role(role: AgentRole) -> list[TeamMember]:
    return [m for m in TEAM_ROSTER if m.role == role]


def get_developers() -> list[TeamMember]:
    seen: set[str] = set()
    devs: list[TeamMember] = []
    for m in TEAM_ROSTER:
        if m.role not in (
            AgentRole.FRONTEND_DEV,
            AgentRole.BACKEND_DEV,
            AgentRole.FULLSTACK_DEV,
            AgentRole.MOBILE_DEV,
            AgentRole.APP_DEVELOPER,
        ):
            continue
        if m.name in seen:
            continue
        seen.add(m.name)
        devs.append(m)
    return devs


def get_social_team() -> list[TeamMember]:
    seen: set[str] = set()
    team: list[TeamMember] = []
    for m in TEAM_ROSTER:
        if m.role not in (
            AgentRole.SOCIAL_TEAM_LEADER,
            AgentRole.SOCIAL_MEDIA_EXECUTIVE,
            AgentRole.SOCIAL_MEDIA_ANALYST,
            AgentRole.SOCIAL_MEDIA_COORDINATOR,
            AgentRole.GRAPHIC_DESIGNER,
            AgentRole.GRAPHIC_DESIGNER_2,
        ):
            continue
        if m.name in seen:
            continue
        seen.add(m.name)
        team.append(m)
    return team


def is_social_team_member(name: str) -> bool:
    return name in frozenset(m.name for m in get_social_team())


def canonical_office_roster() -> list[TeamMember]:
    """One roster entry per person — social roles win for the social media team."""
    social_by_name = {m.name: m for m in get_social_team()}
    by_name: dict[str, TeamMember] = dict(social_by_name)
    for member in TEAM_ROSTER:
        if member.name in social_by_name:
            continue
        if member.name not in by_name:
            by_name[member.name] = member
    return list(by_name.values())


def get_graphic_designers() -> list[TeamMember]:
    designers: list[TeamMember] = []
    for role in (AgentRole.GRAPHIC_DESIGNER, AgentRole.GRAPHIC_DESIGNER_2):
        try:
            designers.append(get_member_by_role(role))
        except ValueError:
            pass
    return designers
