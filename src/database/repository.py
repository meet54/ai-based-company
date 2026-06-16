import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.database.models import ActivityLogDB, PaymentDB, ProjectDB, QuotationDB, Base
from src.models.schemas import (
    ActivityLog,
    AgentRole,
    DashboardStats,
    Payment,
    Project,
    ProjectStage,
    ProjectStatus,
    Quotation,
)


engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from src.database.state_store import ensure_sync_tables, migrate_json_to_database

    ensure_sync_tables()
    migrate_json_to_database()


def _parse_devs(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def _project_from_db(row: ProjectDB) -> Project:
    return Project(
        id=row.id,
        title=row.title,
        client_company=row.client_company,
        client_name=row.client_name,
        client_email=row.client_email,
        description=row.description,
        requirements=row.requirements or "",
        deliverables=row.deliverables or "",
        tech_stack=row.tech_stack or "",
        current_stage=ProjectStage(row.current_stage),
        status=ProjectStatus(row.status),
        assigned_developers=_parse_devs(row.assigned_developers),
        quotation_total=row.quotation_total,
        payment_status=row.payment_status,
        ceo_notes=row.ceo_notes or "",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class Database:
    async def create_project(self, project: Project) -> Project:
        async with async_session() as session:
            row = ProjectDB(
                title=project.title,
                client_company=project.client_company,
                client_name=project.client_name,
                client_email=project.client_email,
                description=project.description,
                requirements=project.requirements,
                deliverables=project.deliverables,
                tech_stack=project.tech_stack,
                current_stage=project.current_stage.value,
                status=project.status.value,
                assigned_developers=json.dumps(project.assigned_developers),
                quotation_total=project.quotation_total,
                payment_status=project.payment_status,
                ceo_notes=project.ceo_notes,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _project_from_db(row)

    async def get_project(self, project_id: int) -> Optional[Project]:
        async with async_session() as session:
            result = await session.execute(select(ProjectDB).where(ProjectDB.id == project_id))
            row = result.scalar_one_or_none()
            return _project_from_db(row) if row else None

    async def list_projects(self) -> list[Project]:
        async with async_session() as session:
            result = await session.execute(select(ProjectDB).order_by(ProjectDB.updated_at.desc()))
            return [_project_from_db(r) for r in result.scalars().all()]

    async def update_project(self, project: Project) -> Project:
        async with async_session() as session:
            result = await session.execute(select(ProjectDB).where(ProjectDB.id == project.id))
            row = result.scalar_one()
            row.title = project.title
            row.client_company = project.client_company
            row.client_name = project.client_name
            row.client_email = project.client_email
            row.description = project.description
            row.requirements = project.requirements
            row.deliverables = project.deliverables
            row.tech_stack = project.tech_stack
            row.current_stage = project.current_stage.value
            row.status = project.status.value
            row.assigned_developers = json.dumps(project.assigned_developers)
            row.quotation_total = project.quotation_total
            row.payment_status = project.payment_status
            row.ceo_notes = project.ceo_notes
            row.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(row)
            return _project_from_db(row)

    async def save_quotation(self, quotation: Quotation) -> Quotation:
        async with async_session() as session:
            row = QuotationDB(
                project_id=quotation.project_id,
                line_items=quotation.line_items,
                subtotal=quotation.subtotal,
                tax_percent=quotation.tax_percent,
                tax_amount=quotation.tax_amount,
                total_amount=quotation.total_amount,
                currency=quotation.currency,
                valid_until=quotation.valid_until,
                notes=quotation.notes,
                approved_by_ceo=quotation.approved_by_ceo,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            quotation.id = row.id
            return quotation

    async def get_quotation(self, project_id: int) -> Optional[Quotation]:
        async with async_session() as session:
            result = await session.execute(
                select(QuotationDB)
                .where(QuotationDB.project_id == project_id)
                .order_by(QuotationDB.created_at.desc())
            )
            row = result.scalars().first()
            if not row:
                return None
            return Quotation(
                id=row.id,
                project_id=row.project_id,
                line_items=row.line_items,
                subtotal=row.subtotal,
                tax_percent=row.tax_percent,
                tax_amount=row.tax_amount,
                total_amount=row.total_amount,
                currency=row.currency,
                valid_until=row.valid_until,
                notes=row.notes,
                approved_by_ceo=row.approved_by_ceo,
                created_at=row.created_at,
            )

    async def approve_quotation(self, project_id: int) -> None:
        async with async_session() as session:
            result = await session.execute(
                select(QuotationDB)
                .where(QuotationDB.project_id == project_id)
                .order_by(QuotationDB.created_at.desc())
            )
            row = result.scalars().first()
            if row:
                row.approved_by_ceo = True
                await session.commit()

    async def save_payment(self, payment: Payment) -> Payment:
        async with async_session() as session:
            row = PaymentDB(
                project_id=payment.project_id,
                amount=payment.amount,
                currency=payment.currency,
                status=payment.status,
                payment_method=payment.payment_method,
                ceo_account=payment.ceo_account,
                received_at=payment.received_at,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            payment.id = row.id
            return payment

    async def get_payment(self, project_id: int) -> Optional[Payment]:
        async with async_session() as session:
            result = await session.execute(
                select(PaymentDB).where(PaymentDB.project_id == project_id)
            )
            row = result.scalar_one_or_none()
            if not row:
                return None
            return Payment(
                id=row.id,
                project_id=row.project_id,
                amount=row.amount,
                currency=row.currency,
                status=row.status,
                payment_method=row.payment_method,
                ceo_account=row.ceo_account,
                received_at=row.received_at,
                created_at=row.created_at,
            )

    async def log_activity(self, log: ActivityLog) -> ActivityLog:
        async with async_session() as session:
            row = ActivityLogDB(
                project_id=log.project_id,
                agent_role=log.agent_role.value,
                agent_name=log.agent_name,
                action=log.action,
                details=log.details,
                stage=log.stage.value if log.stage else None,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            log.id = row.id
            return log

    async def get_activity_logs(self, project_id: Optional[int] = None, limit: int = 50) -> list[ActivityLog]:
        async with async_session() as session:
            query = select(ActivityLogDB).order_by(ActivityLogDB.created_at.desc()).limit(limit)
            if project_id:
                query = query.where(ActivityLogDB.project_id == project_id)
            result = await session.execute(query)
            logs = []
            for row in result.scalars().all():
                logs.append(
                    ActivityLog(
                        id=row.id,
                        project_id=row.project_id,
                        agent_role=AgentRole(row.agent_role),
                        agent_name=row.agent_name,
                        action=row.action,
                        details=row.details,
                        stage=ProjectStage(row.stage) if row.stage else None,
                        created_at=row.created_at,
                    )
                )
            return logs

    async def get_dashboard_stats(self, team_size: int) -> DashboardStats:
        async with async_session() as session:
            total = await session.scalar(select(func.count()).select_from(ProjectDB)) or 0
            active = await session.scalar(
                select(func.count()).select_from(ProjectDB).where(ProjectDB.status == "active")
            ) or 0
            completed = await session.scalar(
                select(func.count()).select_from(ProjectDB).where(ProjectDB.status == "completed")
            ) or 0
            pending_approvals = await session.scalar(
                select(func.count())
                .select_from(ProjectDB)
                .where(ProjectDB.current_stage == ProjectStage.CEO_APPROVAL.value)
            ) or 0
            revenue = await session.scalar(
                select(func.coalesce(func.sum(PaymentDB.amount), 0.0)).where(PaymentDB.status == "received")
            ) or 0.0
            pending = await session.scalar(
                select(func.coalesce(func.sum(PaymentDB.amount), 0.0)).where(PaymentDB.status == "pending")
            ) or 0.0
            return DashboardStats(
                total_projects=total,
                active_projects=active,
                completed_projects=completed,
                pending_approvals=pending_approvals,
                total_revenue=float(revenue),
                pending_payments=float(pending),
                team_size=team_size,
            )


db = Database()
