from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional
import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent.parent
from pydantic import BaseModel

from src.agents.team import TEAM_ROSTER
from src.api.auth import (
    ceo_auth_middleware,
    clear_session_cookie,
    credentials_valid,
    is_authenticated,
    set_session_cookie,
)
from src.config import settings
from src.database.repository import db, init_db
from src.models.schemas import (
    CEOApprovalRequest,
    ClientInquiryRequest,
    CreateProjectRequest,
    Project,
    ProjectStage,
    ProjectStatus,
)
from src.services.code_generator import code_generator
from src.services.idle_worker import idle_worker
from src.services.lead_scout import lead_scout
from src.services.lead_scout_worker import lead_scout_worker
from src.services.office_social_worker import office_social_worker
from src.services.pricing import classify_tier, get_tier, list_tiers
from src.services.requirements import extract_client_brief
from src.services.site_builder import parse_site_spec
from src.services.team_monitor import team_monitor
from src.services.walkgether import walkgether
from src.walkgether.repository import walkgether_db
from src.walkgether.router import router as walkgether_router
from src.workflow.engine import workflow


def _enrich_project(project_dict: dict) -> dict:
    pid = project_dict.get("id")
    is_done = (
        project_dict.get("status") == "completed"
        or project_dict.get("current_stage") == "project_closed"
    )
    preview_available = bool(pid and code_generator.has_preview(pid))
    return {
        **project_dict,
        "is_done": is_done,
        "preview_available": preview_available,
        "preview_url": code_generator.preview_url(pid) if preview_available else None,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await walkgether_db.init()
    await walkgether_db.seed_demo_users()
    walkgether.init()
    worker = asyncio.create_task(idle_worker.start())
    lead_worker = asyncio.create_task(lead_scout_worker.start())
    social_worker = asyncio.create_task(office_social_worker.start())
    yield
    idle_worker.stop()
    lead_scout_worker.stop()
    office_social_worker.stop()
    worker.cancel()
    lead_worker.cancel()
    social_worker.cancel()
    try:
        await worker
    except asyncio.CancelledError:
        pass
    try:
        await lead_worker
    except asyncio.CancelledError:
        pass
    try:
        await social_worker
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.company_name,
    description="AI-powered IT company — CEO command center",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(walkgether_router)
app.middleware("http")(ceo_auth_middleware)


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
async def ceo_login(req: LoginRequest):
    if not credentials_valid(req.email, req.password):
        raise HTTPException(401, "Invalid email or password")
    response = JSONResponse({"ok": True, "ceo_name": settings.ceo_name})
    set_session_cookie(response, req.email)
    return response


@app.post("/api/auth/logout")
async def ceo_logout():
    response = JSONResponse({"ok": True})
    clear_session_cookie(response)
    return response


@app.get("/api/auth/session")
async def ceo_session(request: Request):
    if not is_authenticated(request):
        raise HTTPException(401, "Not authenticated")
    return {
        "authenticated": True,
        "ceo_name": settings.ceo_name,
        "ceo_email": settings.ceo_email,
    }


@app.get("/api/auth/info")
async def auth_info():
    return {
        "company_name": settings.company_name,
        "ceo_name": settings.ceo_name,
    }


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=503, content={"detail": str(exc)})

app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/login")
async def login_page():
    return FileResponse(ROOT / "static" / "login.html")


@app.get("/")
async def root():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/client")
async def client_portal():
    return FileResponse(ROOT / "static" / "client.html")


@app.get("/preview/{project_id}")
async def preview_project(project_id: int):
    if not code_generator.has_preview(project_id):
        raise HTTPException(404, "No preview available for this project")
    from fastapi.responses import HTMLResponse
    content = code_generator.read_file(project_id, "index.html")
    return HTMLResponse(content)


@app.get("/walkgether/app")
async def walkgether_app_redirect():
    return RedirectResponse(url="/walkgether/app/", status_code=307)


@app.get("/walkgether/app/")
async def walkgether_app():
    return FileResponse(ROOT / "deliverables" / "inhouse" / "walkgether" / "app" / "index.html")


@app.get("/walkgether/app/{file_path:path}")
async def walkgether_app_assets(file_path: str):
    base = ROOT / "deliverables" / "inhouse" / "walkgether" / "app"
    target = (base / file_path).resolve()
    if not str(target).startswith(str(base.resolve())):
        raise HTTPException(400, "Invalid path")
    if not target.is_file():
        raise HTTPException(404, "Not found")
    return FileResponse(target)


@app.get("/deliverables/inhouse/walkgether/{file_path:path}")
async def serve_walkgether(file_path: str):
    try:
        content = walkgether.read_file(file_path)
    except ValueError:
        raise HTTPException(400, "Invalid path")
    except FileNotFoundError:
        raise HTTPException(404, "File not found")
    if file_path.endswith(".html"):
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content)
    return FileResponse(
        ROOT / "deliverables" / "inhouse" / "walkgether" / file_path,
        filename=Path(file_path).name,
    )


@app.get("/api/inhouse/walkgether")
async def get_walkgether_status():
    return walkgether.get_status()


@app.get("/api/inhouse/walkgether/files")
async def list_walkgether_files():
    return {
        "project": "walkgether",
        "directory": "deliverables/inhouse/walkgether",
        "files": walkgether.list_files(),
    }


@app.get("/deliverables/{project_id}/{file_path:path}")
async def serve_deliverable(project_id: int, file_path: str):
    try:
        content = code_generator.read_file(project_id, file_path)
    except ValueError:
        raise HTTPException(400, "Invalid path")
    except FileNotFoundError:
        raise HTTPException(404, "File not found")
    if file_path.endswith(".html"):
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content)
    return FileResponse(
        code_generator.project_dir(project_id) / file_path,
        filename=Path(file_path).name,
    )


@app.get("/api/company")
async def company_info():
    return {
        "name": settings.company_name,
        "ceo_name": settings.ceo_name,
        "ceo_email": settings.ceo_email,
        "demo_mode": settings.use_demo,
        "ai_mode": settings.ai_mode,
        "provider": settings.active_provider,
        "model": settings.active_model if settings.has_api_key else None,
        "workflow_stages": [s.value for s in ProjectStage],
    }


@app.get("/api/team")
async def get_team():
    return [m.model_dump() for m in TEAM_ROSTER]


@app.get("/api/team/live")
async def get_team_live():
    logs = await db.get_activity_logs(limit=200)
    projects = await db.list_projects()
    project_map = {p.id: p.title for p in projects}
    activity_by_agent: dict[str, dict] = {}
    for log in logs:
        name = log.agent_name
        if name not in activity_by_agent:
            project_title = None
            if log.project_id:
                project_title = project_map.get(log.project_id)
            elif log.action.startswith("Walkgether:"):
                project_title = "Walkgether (In-House)"
            activity_by_agent[name] = {
                "action": log.action,
                "details": log.details,
                "project_id": log.project_id,
                "stage": log.stage.value if log.stage else None,
                "created_at": log.created_at.isoformat(),
                "project_title": project_title,
            }
    for name, act in activity_by_agent.items():
        if act.get("project_id") and not act.get("project_title"):
            act["project_title"] = project_map.get(act["project_id"])

    roster, working_count = team_monitor.build_live_roster(activity_by_agent)
    active_projects = [p for p in projects if p.status.value == "active"]
    inhouse_working = sum(1 for m in roster if m.get("inhouse") and m.get("status") == "working")
    return {
        "members": roster,
        "working_count": working_count,
        "idle_count": len(roster) - working_count,
        "active_projects": len(active_projects),
        "inhouse_project": walkgether.get_status(),
        "inhouse_working": inhouse_working,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/dashboard")
async def dashboard():
    stats = await db.get_dashboard_stats(team_size=len(TEAM_ROSTER))
    projects = await db.list_projects()
    logs = await db.get_activity_logs(limit=20)
    enriched = [_enrich_project(p.model_dump()) for p in projects]
    ready = [p for p in enriched if p["is_done"] and p["preview_available"]]
    return {
        "stats": stats.model_dump(),
        "recent_projects": enriched[:5],
        "recent_activity": [l.model_dump() for l in logs],
        "notifications": {
            "completed_ready": len(ready),
            "projects": ready[:10],
        },
        "inhouse": {
            "walkgether": walkgether.get_status(),
        },
        "leads": {
            "status": lead_scout.get_status(),
            "items": lead_scout.list_leads(status="new", limit=8),
        },
    }


@app.get("/api/pricing/tiers")
async def get_pricing_tiers():
    return {"currency": "USD", "tiers": list_tiers()}


@app.get("/api/leads/live")
async def get_live_leads():
    return {
        "status": lead_scout.get_status(),
        "leads": lead_scout.list_leads(status="new", limit=30),
    }


@app.post("/api/leads/scan")
async def scan_leads():
    return await lead_scout.scan()


@app.post("/api/leads/{lead_id}/dismiss")
async def dismiss_lead(lead_id: str):
    if not lead_scout.dismiss_lead(lead_id):
        raise HTTPException(404, "Lead not found")
    return {"ok": True}


@app.post("/api/leads/{lead_id}/approach")
async def approach_lead(lead_id: str):
    """Convert a discovered lead into a client project and start the AI pipeline."""
    lead = lead_scout.get_lead(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    if lead.get("status") == "converted":
        raise HTTPException(400, "Lead already converted")

    source_note = f"Source: {lead.get('platform_label')} · {lead.get('url', '')}"
    pricing = lead.get("pricing_estimate") or {}
    tier_id = pricing.get("tier_id") or classify_tier(f"{lead['title']} {lead['description']}")

    project = Project(
        title=f"{lead['company_name']} — {lead['title'][:60]}",
        client_company=lead["company_name"],
        client_name=lead["contact_name"],
        client_email=lead["contact_email"],
        description=f"{lead['description']}\n\n---\n{source_note}",
        pricing_tier=tier_id,
        source_type="freelance_lead",
        current_stage=ProjectStage.LEAD_GENERATION,
        status=ProjectStatus.ACTIVE,
        ceo_notes=f"Discovered via {lead.get('platform_label')} · Est. ${pricing.get('estimated_usd', 0):,.0f} USD",
    )
    created = await db.create_project(project)
    lead_scout.mark_converted(lead_id, created.id)
    result = await workflow.run_full_pipeline(created.id, stop_at_ceo=True)
    quotation = await db.get_quotation(created.id)
    return {
        "message": f"Approaching {lead['company_name']} — pipeline started!",
        "lead_id": lead_id,
        "approach_urls": lead.get("approach_urls", {}),
        "outreach_draft": lead.get("outreach_draft", ""),
        "pricing_estimate": pricing,
        "quotation": quotation.model_dump() if quotation else None,
        **result,
    }


@app.get("/api/projects")
async def list_projects():
    projects = await db.list_projects()
    return [_enrich_project(p.model_dump()) for p in projects]


@app.get("/api/projects/{project_id}")
async def get_project(project_id: int):
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    quotation = await db.get_quotation(project_id)
    payment = await db.get_payment(project_id)
    logs = await db.get_activity_logs(project_id=project_id, limit=100)
    return {
        "project": _enrich_project(project.model_dump()),
        "quotation": quotation.model_dump() if quotation else None,
        "payment": payment.model_dump() if payment else None,
        "activity": [l.model_dump() for l in logs],
    }


@app.post("/api/projects")
async def create_project(req: CreateProjectRequest):
    tier_id = classify_tier(req.description)
    project = Project(
        title=req.title,
        client_company=req.client_company,
        client_name=req.client_name,
        client_email=req.client_email,
        description=req.description,
        pricing_tier=tier_id,
        source_type="manual",
        current_stage=ProjectStage.LEAD_GENERATION,
        status=ProjectStatus.ACTIVE,
    )
    created = await db.create_project(project)
    result = await workflow.run_full_pipeline(created.id, stop_at_ceo=True)
    return result


@app.post("/api/projects/{project_id}/run-stage")
async def run_stage(project_id: int):
    try:
        from src.services.llm import llm_service
        llm_service._rate_limit_hit = False
        result = await workflow.run_stage(project_id)
        if llm_service.using_fallback:
            result["warning"] = "Groq limit reached — demo responses used for this stage."
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/projects/{project_id}/run-all")
async def run_all_stages(project_id: int):
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if project.current_stage == ProjectStage.CEO_APPROVAL:
        raise HTTPException(400, "CEO approval required first")
    try:
        from src.services.llm import llm_service
        llm_service._rate_limit_hit = False
        result = await workflow.run_full_pipeline(project_id, stop_at_ceo=False)
        if llm_service.using_fallback:
            result["warning"] = "Groq daily limit reached — completed with demo AI. Try again tomorrow for real AI."
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/projects/{project_id}/requote")
async def requote_project(project_id: int):
    """Recalculate quotation using fixed USD tier pricing."""
    try:
        return await workflow.regenerate_quotation(project_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/projects/{project_id}/ceo-approve")
async def ceo_approve(project_id: int, req: CEOApprovalRequest):
    try:
        return await workflow.ceo_approve(project_id, req.approved, req.notes)
    except ValueError as e:
        raise HTTPException(400, str(e))


class SimulateLeadRequest(BaseModel):
    company_name: str = "TechStart Inc."
    contact_name: str = "John Smith"
    contact_email: str = "john@techstart.com"
    need: str = "We need a modern e-commerce website with payment integration"


@app.post("/api/simulate-lead")
async def simulate_lead(req: SimulateLeadRequest):
    """Marketing + Sales finds a new client automatically."""
    project = Project(
        title=f"{req.company_name} — {req.need[:50]}",
        client_company=req.company_name,
        client_name=req.contact_name,
        client_email=req.contact_email,
        description=req.need,
        pricing_tier=classify_tier(req.need),
        source_type="simulated",
        current_stage=ProjectStage.LEAD_GENERATION,
        status=ProjectStatus.ACTIVE,
    )
    created = await db.create_project(project)
    result = await workflow.run_full_pipeline(created.id, stop_at_ceo=True)
    return {
        "message": f"New lead from {req.company_name}! Pipeline started.",
        **result,
    }


@app.post("/api/projects/{project_id}/regenerate-preview")
async def regenerate_preview(project_id: int):
    """Rebuild preview from parsed client requirements."""
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    result = code_generator.write_premium_site(project)
    return {
        "message": f"Site rebuilt from client requirements for {project.title}",
        "preview_url": code_generator.preview_url(project_id),
        "spec": {
            k: getattr(parse_site_spec(project), k)
            for k in (
                "wants_carousel", "wants_about", "wants_contact",
                "wants_ecommerce", "brand_name", "owner_name",
            )
        },
        **result,
    }


@app.get("/api/projects/{project_id}/files")
async def list_project_files(project_id: int):
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return {
        "project_id": project_id,
        "directory": f"deliverables/project-{project_id}",
        "files": code_generator.list_files(project_id),
    }


@app.get("/api/projects/{project_id}/files/{file_path:path}")
async def get_project_file(project_id: int, file_path: str):
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    try:
        content = code_generator.read_file(project_id, file_path)
        return {"path": file_path, "content": content}
    except ValueError:
        raise HTTPException(400, "Invalid path")
    except FileNotFoundError:
        raise HTTPException(404, "File not found")


@app.post("/api/client-inquiry")
async def client_inquiry(req: ClientInquiryRequest):
    """Public form — real clients submit project requests."""
    type_labels = {
        "website": "Website",
        "webapp": "Web Application",
        "mobile": "Mobile App",
        "ecommerce": "E-Commerce",
        "custom": "Custom Software",
        "single_page": "Single Page Website",
        "dynamic_2_page": "Dynamic 2-Page Website",
    }
    tier_id = req.service_tier or classify_tier(
        f"{req.description} {req.must_have_features}",
        project_type=req.project_type,
    )
    tier = get_tier(tier_id)
    project_type = type_labels.get(req.project_type, req.project_type)
    title = f"{req.company_name} — {tier.label if tier else project_type}"

    description_parts = [req.description]
    if req.pages_needed:
        description_parts.append(f"Pages needed: {req.pages_needed}")
    if req.must_have_features:
        description_parts.append(f"Must-have features: {req.must_have_features}")
    if req.budget_range:
        description_parts.append(f"Budget: {req.budget_range}")
    if req.timeline:
        description_parts.append(f"Timeline: {req.timeline}")
    if req.phone:
        description_parts.append(f"Phone: {req.phone}")

    brief = extract_client_brief("\n".join(description_parts), title)

    project = Project(
        title=title,
        client_company=req.company_name,
        client_name=req.contact_name,
        client_email=req.contact_email,
        description="\n".join(description_parts),
        pricing_tier=tier_id,
        source_type="client_inquiry",
        current_stage=ProjectStage.LEAD_GENERATION,
        status=ProjectStatus.ACTIVE,
        ceo_notes=f"Public inquiry · Tier: {tier.label if tier else tier_id} · Est. ${tier.base_usd if tier else 0:,.0f} USD",
    )
    created = await db.create_project(project)
    result = await workflow.run_full_pipeline(created.id, stop_at_ceo=True)
    quotation = await db.get_quotation(created.id)
    est = tier.base_usd if tier else 0
    return {
        "success": True,
        "message": (
            f"Thank you {req.contact_name}! Your request has been received. "
            f"Our team is preparing a quotation (typically from ${est:,.0f} USD for {tier.label if tier else 'your project type'}). "
            f"We will follow up at {req.contact_email}."
        ),
        "project_id": created.id,
        "pricing_tier": tier_id,
        "estimated_usd": est,
        "requirements_preview": brief,
        "quotation": quotation.model_dump() if quotation else None,
        **result,
    }


@app.get("/api/activity")
async def get_activity(project_id: Optional[int] = None, limit: int = 50):
    logs = await db.get_activity_logs(project_id=project_id, limit=limit)
    return [l.model_dump() for l in logs]
