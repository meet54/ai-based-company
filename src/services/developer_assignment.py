"""Assign developers based on project tier and tech stack."""

from __future__ import annotations

from src.agents.team import TEAM_ROSTER, get_developers
from src.models.schemas import AgentRole, Project
from src.services.pricing import classify_tier, get_tier


def assign_developers(project: Project) -> list[str]:
    tier_id = getattr(project, "pricing_tier", "") or classify_tier(
        f"{project.title} {project.description} {project.requirements}"
    )
    stack = (project.tech_stack or "").lower()
    blob = f"{project.title} {project.description} {project.requirements}".lower()

    devs_by_role = {m.role: m for m in get_developers()}
    fe = devs_by_role.get(AgentRole.FRONTEND_DEV)
    be = devs_by_role.get(AgentRole.BACKEND_DEV)
    fs = devs_by_role.get(AgentRole.FULLSTACK_DEV)
    mobile = devs_by_role.get(AgentRole.MOBILE_DEV)
    app_dev = devs_by_role.get(AgentRole.APP_DEVELOPER)

    assigned: list[str] = []

    if tier_id == "mobile_app" or "mobile" in blob or "react native" in stack:
        if mobile:
            assigned.append(mobile.name)
        if app_dev and app_dev.name not in assigned:
            assigned.append(app_dev.name)
        if be and len(assigned) < 3:
            assigned.append(be.name)
    elif tier_id in ("custom_software", "web_application"):
        if fs:
            assigned.append(fs.name)
        if be and be.name not in assigned:
            assigned.append(be.name)
        if fe and fe.name not in assigned:
            assigned.append(fe.name)
    elif tier_id == "ecommerce_starter":
        if fs:
            assigned.append(fs.name)
        if fe and fe.name not in assigned:
            assigned.append(fe.name)
        if be and be.name not in assigned:
            assigned.append(be.name)
    else:
        if fe:
            assigned.append(fe.name)
        if fs and fs.name not in assigned:
            assigned.append(fs.name)
        if be and be.name not in assigned:
            assigned.append(be.name)

    if not assigned:
        assigned = [d.name for d in get_developers()[:3]]

    tier = get_tier(tier_id)
    if tier and tier.id in ("single_page", "dynamic_2_page") and len(assigned) > 2:
        assigned = assigned[:2]

    return assigned[:3]
