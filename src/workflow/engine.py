import json
import re
from datetime import datetime

from src.agents.base import get_agent
from src.agents.prompts import STAGE_AGENTS
from src.agents.team import TEAM_ROSTER, get_member_by_role
from src.config import settings
from src.services.code_generator import code_generator
from src.services.developer_assignment import assign_developers
from src.services.pricing import build_quotation, classify_tier, get_tier
from src.services.requirements import format_requirements_document
from src.services.team_monitor import team_monitor
from src.services.workflow_lock import workflow_lock
from src.database.repository import db
from src.models.schemas import (
    ActivityLog,
    AgentRole,
    Payment,
    Project,
    ProjectStage,
    ProjectStatus,
    Quotation,
    STAGE_ORDER,
)


STAGE_TASKS: dict[ProjectStage, str] = {
    ProjectStage.LEAD_GENERATION: (
        "Generate marketing leads and qualify the client inquiry. "
        "Identify the client's industry, needs, and potential project value."
    ),
    ProjectStage.REQUIREMENT_GATHERING: (
        "Conduct a thorough requirements discovery session with the client. "
        "Document functional requirements, pages, integrations, timeline, and acceptance criteria. "
        "Use ONLY the client's stated needs — do not invent features they did not ask for."
    ),
    ProjectStage.QUOTATION: (
        "Prepare quotation notes aligned to our USD service tiers. "
        "Do not exceed tier base pricing unless add-ons are clearly justified. "
        "Return JSON with line_items array (item, amount fields)."
    ),
    ProjectStage.CEO_APPROVAL: (
        "Quotation is ready for CEO review. Awaiting CEO approval before project kickoff."
    ),
    ProjectStage.PROJECT_KICKOFF: (
        "Plan the project: assign developers, create sprint plan, and set milestones."
    ),
    ProjectStage.DEVELOPMENT: (
        "Build the website or software EXACTLY per the requirements document. "
        "For websites: include carousel only if requested, about us if requested, "
        "contact form if requested, client name in footer. "
        "Do NOT add product/shop pages unless the client asked for ecommerce. "
        "Never paste budget, phone, or timeline into visible page text."
    ),
    ProjectStage.TEAM_LEADER_REVIEW: (
        "Cross-check all deliverables against requirements. "
        "Review code quality, completeness, and approve or request changes."
    ),
    ProjectStage.QA_TESTING: (
        "Execute comprehensive testing. Report test cases, bugs, and pass/fail verdict."
    ),
    ProjectStage.CLIENT_HANDOVER: (
        "Prepare and deliver the handover package to the client. "
        "Include documentation, training, and obtain client sign-off."
    ),
    ProjectStage.PAYMENT_COLLECTION: (
        "Generate invoice and track payment to CEO account. "
        "Confirm payment receipt status."
    ),
    ProjectStage.PROJECT_CLOSED: (
        "Close the project. Summarize outcomes, lessons learned, and archive deliverables."
    ),
}


class WorkflowEngine:
    async def run_stage(self, project_id: int) -> dict:
        await workflow_lock.acquire()
        try:
            return await self._run_stage_impl(project_id)
        finally:
            workflow_lock.release()

    async def _run_stage_impl(self, project_id: int) -> dict:
        project = await db.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        stage = project.current_stage

        if stage == ProjectStage.CEO_APPROVAL:
            return {
                "status": "awaiting_ceo",
                "message": "Quotation ready. CEO approval required to proceed.",
                "project": project.model_dump(),
            }

        if stage == ProjectStage.PROJECT_CLOSED:
            return {
                "status": "completed",
                "message": "Project is already closed.",
                "project": project.model_dump(),
            }

        results = await self._execute_stage(project, stage)
        project = await self._advance_project(project, stage, results)

        return {
            "status": "success",
            "stage_completed": stage.value,
            "next_stage": project.current_stage.value,
            "agent_outputs": results,
            "project": project.model_dump(),
        }

    async def ceo_approve(self, project_id: int, approved: bool, notes: str = "") -> dict:
        await workflow_lock.acquire()
        try:
            return await self._ceo_approve_impl(project_id, approved, notes)
        finally:
            workflow_lock.release()

    async def _ceo_approve_impl(self, project_id: int, approved: bool, notes: str = "") -> dict:
        project = await db.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        if project.current_stage != ProjectStage.CEO_APPROVAL:
            raise ValueError("Project is not awaiting CEO approval")

        project.ceo_notes = notes

        if not approved:
            project.current_stage = ProjectStage.QUOTATION
            project.status = ProjectStatus.ON_HOLD
            await db.update_project(project)
            await self._log(
                project.id,
                AgentRole.CEO,
                settings.ceo_name,
                "Quotation Rejected",
                f"CEO rejected quotation. Notes: {notes}",
                ProjectStage.CEO_APPROVAL,
            )
            return {"status": "rejected", "project": project.model_dump()}

        await db.approve_quotation(project.id)
        project.current_stage = ProjectStage.PROJECT_KICKOFF
        await db.update_project(project)
        await self._log(
            project.id,
            AgentRole.CEO,
            settings.ceo_name,
            "Quotation Approved",
            f"CEO approved quotation. Notes: {notes}",
            ProjectStage.CEO_APPROVAL,
        )

        return await self._run_stage_impl(project_id)

    async def _execute_stage(self, project: Project, stage: ProjectStage) -> list[dict]:
        roles = STAGE_AGENTS.get(stage.value, [])
        task = STAGE_TASKS[stage]
        results = []
        context = ""

        for role in roles:
            if role == AgentRole.CEO:
                continue
            agent = get_agent(role)
            member = get_member_by_role(role)
            team_monitor.set_working(
                member.name,
                role.value,
                project,
                task,
                f"Working on {stage.value.replace('_', ' ')} for {project.title}",
            )
            response = await agent.execute(task, project, context)
            results.append(
                {
                    "role": response.role.value,
                    "agent_name": response.agent_name,
                    "output": response.content,
                }
            )
            context += f"\n\n--- {response.agent_name} ---\n{response.content[:400]}"

            team_monitor.set_idle(
                response.agent_name,
                role.value,
                f"Completed {stage.value.replace('_', ' ').title()}",
                response.content[:200],
            )

            await self._log(
                project.id,
                response.role,
                response.agent_name,
                f"Completed {stage.value.replace('_', ' ').title()}",
                response.content[:500] + ("..." if len(response.content) > 500 else ""),
                stage,
            )

        await self._apply_stage_updates(project, stage, results)
        return results

    async def _apply_stage_updates(
        self, project: Project, stage: ProjectStage, results: list[dict]
    ) -> None:
        combined = "\n".join(r["output"] for r in results)

        if stage == ProjectStage.REQUIREMENT_GATHERING:
            if not project.pricing_tier:
                project.pricing_tier = classify_tier(
                    f"{project.title} {project.description}",
                    explicit_tier=project.pricing_tier,
                )
            tier = get_tier(project.pricing_tier)
            tier_label = tier.label if tier else ""
            project.requirements = format_requirements_document(
                project.title,
                project.client_name,
                project.description,
                combined,
                tier_label=tier_label,
            )
            ba = get_agent(AgentRole.BUSINESS_ANALYST)
            ba_response = await ba.execute(
                "Expand the requirements doc with user stories and tech stack. "
                "Stay within the agreed service tier scope.",
                project,
                project.requirements,
            )
            project.requirements = format_requirements_document(
                project.title,
                project.client_name,
                project.description,
                ba_response.content,
                tier_label=tier_label,
            )
            tech_match = re.search(
                r"(?:Tech Stack|Recommended Tech)[:\s]*([^\n]+(?:\n- [^\n]+)*)",
                ba_response.content,
                re.I,
            )
            if tech_match:
                project.tech_stack = tech_match.group(1).strip()

        elif stage == ProjectStage.QUOTATION:
            fresh = await db.get_project(project.id)
            if fresh:
                project = fresh
            blob = f"{project.title} {project.description} {project.requirements}"
            project.pricing_tier = classify_tier(
                blob,
                explicit_tier=project.pricing_tier or "",
            )
            quotation = build_quotation(project.id, project, project.pricing_tier)
            await db.save_quotation(quotation)
            project.quotation_total = quotation.total_amount

        elif stage == ProjectStage.PROJECT_KICKOFF:
            project.assigned_developers = assign_developers(project)

        elif stage == ProjectStage.DEVELOPMENT:
            project.deliverables = combined
            code_result = await code_generator.generate(project)
            file_list = "\n".join(f"- {f}" for f in code_result["files_written"])
            project.deliverables += (
                f"\n\n## Generated Code Files ({code_result['file_count']} files)\n"
                f"Location: `{code_result['directory']}/`\n{file_list}"
            )
            await self._log(
                project.id,
                AgentRole.FULLSTACK_DEV,
                "Elena Vasquez",
                "Code files generated",
                f"Wrote {code_result['file_count']} files to {code_result['directory']}/",
                stage,
            )

        elif stage == ProjectStage.PAYMENT_COLLECTION:
            amount = project.quotation_total or 0.0
            payment = Payment(
                project_id=project.id,
                amount=amount,
                status="received",
                ceo_account=f"{settings.ceo_name} — Business Account ({settings.ceo_email})",
                received_at=datetime.utcnow(),
            )
            await db.save_payment(payment)
            project.payment_status = "received"

        await db.update_project(project)

    async def regenerate_quotation(self, project_id: int) -> dict:
        """Rebuild quotation from tier pricing (fixes legacy $15k+ quotes)."""
        project = await db.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        blob = f"{project.title} {project.description} {project.requirements}"
        project.pricing_tier = classify_tier(blob, explicit_tier=project.pricing_tier or "")
        quotation = build_quotation(project.id, project, project.pricing_tier)
        await db.save_quotation(quotation)
        project.quotation_total = quotation.total_amount
        if project.current_stage == ProjectStage.CEO_APPROVAL:
            project.status = ProjectStatus.ACTIVE
        await db.update_project(project)
        return {
            "status": "success",
            "pricing_tier": project.pricing_tier,
            "quotation": quotation.model_dump(),
            "project": project.model_dump(),
        }

    def _extract_line_items(self, content: str) -> list[dict]:
        try:
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("line_items", [])
        except (json.JSONDecodeError, KeyError):
            pass
        return []

    def _parse_quotation(self, project_id: int, content: str) -> Quotation:
        project_stub = Project(
            id=project_id,
            title="",
            client_company="",
            client_name="",
            client_email="",
            description=content,
        )
        return build_quotation(project_id, project_stub, llm_line_items=self._extract_line_items(content))

    async def _advance_project(
        self, project: Project, completed_stage: ProjectStage, results: list[dict]
    ) -> Project:
        idx = STAGE_ORDER.index(completed_stage)
        if idx < len(STAGE_ORDER) - 1:
            project.current_stage = STAGE_ORDER[idx + 1]
            if project.current_stage == ProjectStage.PROJECT_CLOSED:
                project.status = ProjectStatus.COMPLETED
        project.updated_at = datetime.utcnow()
        return await db.update_project(project)

    async def run_full_pipeline(self, project_id: int, stop_at_ceo: bool = True) -> dict:
        stages_run = []
        while True:
            project = await db.get_project(project_id)
            if not project:
                break
            if project.current_stage == ProjectStage.CEO_APPROVAL and stop_at_ceo:
                return {
                    "status": "paused_at_ceo_approval",
                    "stages_completed": stages_run,
                    "project": project.model_dump(),
                }
            if project.current_stage == ProjectStage.PROJECT_CLOSED:
                return {
                    "status": "completed",
                    "stages_completed": stages_run,
                    "project": project.model_dump(),
                }

            result = await self.run_stage(project_id)
            stages_run.append(result.get("stage_completed"))
            if result.get("status") == "awaiting_ceo":
                return {
                    "status": "paused_at_ceo_approval",
                    "stages_completed": stages_run,
                    "project": result["project"],
                }

    async def _log(
        self,
        project_id: int,
        role: AgentRole,
        name: str,
        action: str,
        details: str,
        stage: ProjectStage,
    ) -> None:
        await db.log_activity(
            ActivityLog(
                project_id=project_id,
                agent_role=role,
                agent_name=name,
                action=action,
                details=details,
                stage=stage,
            )
        )


workflow = WorkflowEngine()
