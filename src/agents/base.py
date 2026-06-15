from dataclasses import dataclass

from src.agents.prompts import AGENT_PROMPTS
from src.agents.team import get_member_by_role
from src.config import settings
from src.models.schemas import AgentRole, Project
from src.services.llm import llm_service


@dataclass
class AgentResponse:
    role: AgentRole
    agent_name: str
    content: str


class Agent:
    def __init__(self, role: AgentRole):
        self.role = role
        self.member = get_member_by_role(role)
        self.system_prompt = AGENT_PROMPTS[role]

    async def execute(self, task: str, project: Project, context: str = "") -> AgentResponse:
        user_message = self._build_message(task, project, context)
        content = await llm_service.complete(self.system_prompt, user_message)
        return AgentResponse(role=self.role, agent_name=self.member.name, content=content)

    def _build_message(self, task: str, project: Project, context: str) -> str:
        def clip(text: str, limit: int = 1200) -> str:
            return text[:limit] + ("..." if len(text) > limit else "")

        parts = [
            f"Company: {settings.company_name}",
            f"Project: {project.title}",
            f"Client: {project.client_name} ({project.client_company})",
            f"Description: {clip(project.description, 800)}",
        ]
        if project.requirements:
            parts.append(f"Requirements: {clip(project.requirements)}")
        if project.tech_stack:
            parts.append(f"Tech Stack: {clip(project.tech_stack, 600)}")
        if project.deliverables:
            parts.append(f"Current Deliverables: {clip(project.deliverables)}")
        if context:
            parts.append(f"Context from previous steps:\n{clip(context, 1500)}")
        parts.append(f"\nYour task:\n{task}")
        return "\n".join(parts)


def get_agent(role: AgentRole) -> Agent:
    return Agent(role)
