from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    CEO = "ceo"
    SALES = "sales"
    MARKETING = "marketing"
    HR = "hr"
    BUSINESS_ANALYST = "business_analyst"
    PROJECT_MANAGER = "project_manager"
    FRONTEND_DEV = "frontend_developer"
    BACKEND_DEV = "backend_developer"
    FULLSTACK_DEV = "fullstack_developer"
    MOBILE_DEV = "mobile_developer"
    APP_DEVELOPER = "app_developer"
    QA_TESTER = "qa_tester"
    FINANCE = "finance"
    CLIENT_SUCCESS = "client_success"
    SOCIAL_TEAM_LEADER = "social_team_leader"
    SOCIAL_MEDIA_EXECUTIVE = "social_media_executive"
    SOCIAL_MEDIA_ANALYST = "social_media_analyst"
    GRAPHIC_DESIGNER = "graphic_designer"
    GRAPHIC_DESIGNER_2 = "graphic_designer_2"
    SOCIAL_MEDIA_COORDINATOR = "social_media_coordinator"


class ProjectStage(str, Enum):
    LEAD_GENERATION = "lead_generation"
    REQUIREMENT_GATHERING = "requirement_gathering"
    QUOTATION = "quotation"
    CEO_APPROVAL = "ceo_approval"
    PROJECT_KICKOFF = "project_kickoff"
    DEVELOPMENT = "development"
    CONTENT_STRATEGY = "content_strategy"
    CONTENT_CREATION = "content_creation"
    CLIENT_CONTENT_APPROVAL = "client_content_approval"
    SOCIAL_PUBLISH = "social_publish"
    TEAM_LEADER_REVIEW = "team_leader_review"
    QA_TESTING = "qa_testing"
    CLIENT_HANDOVER = "client_handover"
    PAYMENT_COLLECTION = "payment_collection"
    PROJECT_CLOSED = "project_closed"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


STAGE_ORDER = [
    ProjectStage.LEAD_GENERATION,
    ProjectStage.REQUIREMENT_GATHERING,
    ProjectStage.QUOTATION,
    ProjectStage.CEO_APPROVAL,
    ProjectStage.PROJECT_KICKOFF,
    ProjectStage.DEVELOPMENT,
    ProjectStage.TEAM_LEADER_REVIEW,
    ProjectStage.QA_TESTING,
    ProjectStage.CLIENT_HANDOVER,
    ProjectStage.PAYMENT_COLLECTION,
    ProjectStage.PROJECT_CLOSED,
]

SOCIAL_STAGE_ORDER = [
    ProjectStage.LEAD_GENERATION,
    ProjectStage.REQUIREMENT_GATHERING,
    ProjectStage.QUOTATION,
    ProjectStage.CEO_APPROVAL,
    ProjectStage.PROJECT_KICKOFF,
    ProjectStage.CONTENT_STRATEGY,
    ProjectStage.CONTENT_CREATION,
    ProjectStage.CLIENT_CONTENT_APPROVAL,
    ProjectStage.SOCIAL_PUBLISH,
    ProjectStage.CLIENT_HANDOVER,
    ProjectStage.PAYMENT_COLLECTION,
    ProjectStage.PROJECT_CLOSED,
]


class TeamMember(BaseModel):
    id: str
    name: str
    role: AgentRole
    department: str
    skills: list[str] = Field(default_factory=list)
    is_active: bool = True


class Lead(BaseModel):
    id: Optional[int] = None
    company_name: str
    contact_name: str
    contact_email: str
    source: str = "marketing"
    initial_need: str
    budget_range: Optional[str] = None
    status: str = "new"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Quotation(BaseModel):
    id: Optional[int] = None
    project_id: int
    line_items: list[dict]
    subtotal: float
    tax_percent: float = 18.0
    tax_amount: float
    total_amount: float
    currency: str = "USD"
    valid_until: str
    notes: str = ""
    approved_by_ceo: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Payment(BaseModel):
    id: Optional[int] = None
    project_id: int
    amount: float
    currency: str = "USD"
    status: str = "pending"
    payment_method: str = "bank_transfer"
    ceo_account: str = ""
    received_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ActivityLog(BaseModel):
    id: Optional[int] = None
    project_id: Optional[int] = None
    agent_role: AgentRole
    agent_name: str
    action: str
    details: str
    stage: Optional[ProjectStage] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Project(BaseModel):
    id: Optional[int] = None
    title: str
    client_company: str
    client_name: str
    client_email: str
    description: str
    requirements: str = ""
    deliverables: str = ""
    tech_stack: str = ""
    pricing_tier: str = ""
    source_type: str = ""
    service_category: str = "software"
    current_stage: ProjectStage = ProjectStage.LEAD_GENERATION
    status: ProjectStatus = ProjectStatus.ACTIVE
    assigned_developers: list[str] = Field(default_factory=list)
    assigned_social_team: list[str] = Field(default_factory=list)
    client_content_approved: bool = False
    client_notes: str = ""
    published_platforms: list[str] = Field(default_factory=list)
    quotation_total: Optional[float] = None
    payment_status: str = "pending"
    ceo_notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateProjectRequest(BaseModel):
    title: str
    client_company: str
    client_name: str
    client_email: str
    description: str
    budget_hint: Optional[str] = None
    service_category: str = "software"


class CEOApprovalRequest(BaseModel):
    approved: bool
    notes: str = ""


class ClientContentApprovalRequest(BaseModel):
    approved: bool
    notes: str = ""


class ClientInquiryRequest(BaseModel):
    company_name: str
    contact_name: str
    contact_email: str
    phone: str = ""
    project_type: str = "website"
    service_category: str = ""
    service_tier: str = ""
    description: str
    budget_range: str = ""
    timeline: str = ""
    pages_needed: str = ""
    must_have_features: str = ""


class DashboardStats(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    pending_approvals: int
    total_revenue: float
    pending_payments: float
    team_size: int
