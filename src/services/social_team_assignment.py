"""Assign social media specialists to a campaign project."""

from src.agents.team import get_graphic_designers, get_member_by_role, get_social_team
from src.models.schemas import AgentRole, Project


def assign_social_team(project: Project) -> list[str]:
    names = [m.name for m in get_social_team()]
    for designer in get_graphic_designers():
        if designer.name not in names:
            names.append(designer.name)
    coordinator = get_member_by_role(AgentRole.SOCIAL_MEDIA_COORDINATOR)
    if coordinator.name not in names:
        names.append(coordinator.name)
    return names
