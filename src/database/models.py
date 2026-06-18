from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProjectDB(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    client_company: Mapped[str] = mapped_column(String(255))
    client_name: Mapped[str] = mapped_column(String(255))
    client_email: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str] = mapped_column(Text, default="")
    deliverables: Mapped[str] = mapped_column(Text, default="")
    tech_stack: Mapped[str] = mapped_column(Text, default="")
    pricing_tier: Mapped[str] = mapped_column(String(64), default="")
    source_type: Mapped[str] = mapped_column(String(64), default="")
    service_category: Mapped[str] = mapped_column(String(32), default="software")
    current_stage: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="active")
    assigned_developers: Mapped[Optional[str]] = mapped_column(Text, default="[]")
    assigned_social_team: Mapped[Optional[str]] = mapped_column(Text, default="[]")
    client_content_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    client_notes: Mapped[str] = mapped_column(Text, default="")
    published_platforms: Mapped[Optional[str]] = mapped_column(Text, default="[]")
    quotation_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    payment_status: Mapped[str] = mapped_column(String(32), default="pending")
    ceo_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuotationDB(Base):
    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    line_items: Mapped[str] = mapped_column(JSON)
    subtotal: Mapped[float] = mapped_column(Float)
    tax_percent: Mapped[float] = mapped_column(Float, default=18.0)
    tax_amount: Mapped[float] = mapped_column(Float)
    total_amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    valid_until: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str] = mapped_column(Text, default="")
    approved_by_ceo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PaymentDB(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    payment_method: Mapped[str] = mapped_column(String(64), default="bank_transfer")
    ceo_account: Mapped[str] = mapped_column(String(255), default="")
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ActivityLogDB(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    agent_role: Mapped[str] = mapped_column(String(64))
    agent_name: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(255))
    details: Mapped[str] = mapped_column(Text)
    stage: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OfficeAgentStateDB(Base):
    __tablename__ = "office_agent_states"

    agent_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    zone: Mapped[str] = mapped_column(String(32), default="desk")
    activity: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TeamAgentLiveDB(Base):
    __tablename__ = "team_agent_live"

    agent_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), default="idle")
    role: Mapped[str] = mapped_column(String(64), default="")
    task: Mapped[str] = mapped_column(Text, default="")
    details: Mapped[str] = mapped_column(Text, default="")
    project_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    project_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    inhouse: Mapped[bool] = mapped_column(Boolean, default=False)
    office_activity: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    conversation_partner: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AppStateDB(Base):
    __tablename__ = "app_state"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
