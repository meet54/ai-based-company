from src.models.schemas import AgentRole, TeamMember

TEAM_ROSTER: list[TeamMember] = [
    TeamMember(
        id="sales-001",
        name="Alex Rivera",
        role=AgentRole.SALES,
        department="Sales",
        skills=["lead generation", "client negotiation", "requirement discovery", "CRM"],
    ),
    TeamMember(
        id="mkt-001",
        name="Priya Sharma",
        role=AgentRole.MARKETING,
        department="Marketing",
        skills=["digital marketing", "SEO", "content strategy", "brand awareness"],
    ),
    TeamMember(
        id="hr-001",
        name="Jordan Lee",
        role=AgentRole.HR,
        department="Human Resources",
        skills=["recruitment", "team coordination", "onboarding", "performance tracking"],
    ),
    TeamMember(
        id="ba-001",
        name="Sam Okafor",
        role=AgentRole.BUSINESS_ANALYST,
        department="Business Analysis",
        skills=["requirements analysis", "user stories", "process mapping", "documentation"],
    ),
    TeamMember(
        id="pm-001",
        name="Morgan Chen",
        role=AgentRole.PROJECT_MANAGER,
        department="Project Management",
        skills=["sprint planning", "code review", "quality oversight", "client communication"],
    ),
    TeamMember(
        id="fe-001",
        name="Riya Patel",
        role=AgentRole.FRONTEND_DEV,
        department="Engineering",
        skills=["React", "Vue", "HTML/CSS", "responsive design", "UI implementation"],
    ),
    TeamMember(
        id="be-001",
        name="David Kim",
        role=AgentRole.BACKEND_DEV,
        department="Engineering",
        skills=["Python", "Node.js", "APIs", "databases", "microservices"],
    ),
    TeamMember(
        id="fs-001",
        name="Elena Vasquez",
        role=AgentRole.FULLSTACK_DEV,
        department="Engineering",
        skills=["full-stack development", "React", "Python", "deployment", "architecture"],
    ),
    TeamMember(
        id="mobile-001",
        name="Aisha Khan",
        role=AgentRole.MOBILE_DEV,
        department="Mobile Engineering",
        skills=["React Native", "iOS", "Android", "Expo", "mobile UI/UX"],
    ),
    TeamMember(
        id="mobile-002",
        name="Marcus Johnson",
        role=AgentRole.APP_DEVELOPER,
        department="Mobile Engineering",
        skills=["React Native", "Google Maps", "Firebase", "push notifications", "location services"],
    ),
    TeamMember(
        id="qa-001",
        name="Chris Taylor",
        role=AgentRole.QA_TESTER,
        department="Quality Assurance",
        skills=["manual testing", "automated testing", "bug reporting", "regression testing"],
    ),
    TeamMember(
        id="fin-001",
        name="Nina Brooks",
        role=AgentRole.FINANCE,
        department="Finance",
        skills=["quotation", "invoicing", "payment tracking", "budget estimation"],
    ),
    TeamMember(
        id="cs-001",
        name="Taylor Wright",
        role=AgentRole.CLIENT_SUCCESS,
        department="Client Success",
        skills=["handover documentation", "training", "support", "feedback collection"],
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


def get_developers() -> list[TeamMember]:
    return [
        m
        for m in TEAM_ROSTER
        if m.role
        in (
            AgentRole.FRONTEND_DEV,
            AgentRole.BACKEND_DEV,
            AgentRole.FULLSTACK_DEV,
            AgentRole.MOBILE_DEV,
            AgentRole.APP_DEVELOPER,
        )
    ]
