"""Stage order and role routing for software vs social media projects."""

from src.models.schemas import AgentRole, Project, ProjectStage, SOCIAL_STAGE_ORDER, STAGE_ORDER

SOCIAL_TIER_IDS = frozenset({
    "social_media_starter",
    "social_media_growth",
    "social_media_premium",
})

SOCIAL_KEYWORDS = (
    "social media",
    "instagram",
    "facebook",
    "linkedin",
    "reel",
    "reels",
    "tiktok",
    "ad campaign",
    "paid ads",
    "content calendar",
    "graphic design",
    "social post",
)


def is_social_project(project: Project) -> bool:
    if getattr(project, "service_category", "") == "social_media":
        return True
    if project.pricing_tier in SOCIAL_TIER_IDS:
        return True
    blob = f"{project.title} {project.description} {project.requirements}".lower()
    return any(k in blob for k in SOCIAL_KEYWORDS)


def get_stage_order(project: Project) -> list[ProjectStage]:
    if is_social_project(project):
        return SOCIAL_STAGE_ORDER
    return STAGE_ORDER


def get_stage_agents(stage: ProjectStage, project: Project) -> list[AgentRole]:
    from src.agents.prompts import STAGE_AGENTS, SOCIAL_STAGE_AGENTS

    social = is_social_project(project)
    mapping = SOCIAL_STAGE_AGENTS if social else STAGE_AGENTS
    return list(mapping.get(stage.value, []))
