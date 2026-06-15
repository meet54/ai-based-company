import json
import re
from datetime import datetime, timedelta

from src.config import settings


class LLMService:
    _rate_limit_hit: bool = False

    async def complete(self, system_prompt: str, user_message: str) -> str:
        if settings.use_demo:
            if settings.ai_mode == "missing_key":
                raise RuntimeError(
                    f"No API key for provider '{settings.llm_provider}'. "
                    "Get a free Groq key at https://console.groq.com or "
                    "Gemini key at https://aistudio.google.com/apikey"
                )
            return self._demo_response(system_prompt, user_message)

        user_message = user_message[:6000]

        provider = settings.active_provider
        try:
            if provider == "groq":
                return await self._groq_complete(system_prompt, user_message)
            if provider == "gemini":
                return await self._gemini_complete(system_prompt, user_message)
            return await self._openai_complete(system_prompt, user_message)
        except RuntimeError as e:
            if settings.fallback_on_rate_limit and self._is_rate_limit_error(str(e)):
                self._rate_limit_hit = True
                return self._demo_response(system_prompt, user_message)
            raise

    def _is_rate_limit_error(self, msg: str) -> bool:
        lower = msg.lower()
        return any(k in lower for k in (
            "rate limit", "token limit", "quota", "too many requests",
            "too large", "request too large", "tokens per",
        ))

    @property
    def using_fallback(self) -> bool:
        return self._rate_limit_hit

    def _http_verify(self):
        import certifi
        return certifi.where() if settings.ssl_verify else False

    async def _groq_complete(self, system_prompt: str, user_message: str) -> str:
        import httpx
        from openai import AsyncOpenAI, APIConnectionError, APIStatusError, AuthenticationError, RateLimitError

        try:
            async with httpx.AsyncClient(verify=self._http_verify(), timeout=120.0) as http_client:
                client = AsyncOpenAI(
                    api_key=settings.groq_api_key,
                    base_url="https://api.groq.com/openai/v1",
                    http_client=http_client,
                )
                response = await client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {"role": "system", "content": system_prompt[:2000]},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                    max_tokens=800,
                )
            return response.choices[0].message.content or ""
        except AuthenticationError as e:
            raise RuntimeError("Groq API key is invalid. Get a free key at https://console.groq.com") from e
        except (RateLimitError, APIStatusError) as e:
            code = getattr(e, "status_code", None)
            msg = str(e)
            if code in (413, 429) or "rate_limit" in msg.lower() or "too large" in msg.lower():
                raise RuntimeError(f"Groq limit reached: {msg[:120]}") from e
            raise RuntimeError(f"Groq API error: {msg[:120]}") from e
        except APIConnectionError as e:
            raise RuntimeError("Could not connect to Groq. Set SSL_VERIFY=false in .env if on Windows.") from e

    async def _gemini_complete(self, system_prompt: str, user_message: str) -> str:
        import httpx

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000},
        }
        response = None
        try:
            async with httpx.AsyncClient(verify=self._http_verify(), timeout=120.0) as client:
                response = await client.post(
                    url,
                    params={"key": settings.gemini_api_key},
                    json=payload,
                )
                if response.status_code == 400:
                    raise RuntimeError("Gemini API key is invalid. Get a free key at https://aistudio.google.com/apikey")
                if response.status_code == 429:
                    raise RuntimeError("Gemini rate limit reached. Wait a moment and try again.")
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            body = response.text[:200] if response is not None else "no response"
            raise RuntimeError(f"Unexpected Gemini response: {body}") from e
        except httpx.HTTPError as e:
            raise RuntimeError("Could not connect to Gemini. Set SSL_VERIFY=false in .env if on Windows.") from e

    async def _openai_complete(self, system_prompt: str, user_message: str) -> str:
        import httpx
        from openai import AsyncOpenAI, APIConnectionError, AuthenticationError, RateLimitError

        verify = self._http_verify()
        try:
            async with httpx.AsyncClient(verify=verify, timeout=120.0) as http_client:
                client = AsyncOpenAI(api_key=settings.openai_api_key, http_client=http_client)
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )
            return response.choices[0].message.content or ""
        except AuthenticationError as e:
            raise RuntimeError(
                "OpenAI API key is invalid. Check OPENAI_API_KEY in your .env file."
            ) from e
        except RateLimitError as e:
            if "insufficient_quota" in str(e).lower() or "quota" in str(e).lower():
                raise RuntimeError(
                    "OpenAI account has no credits. Add billing at "
                    "https://platform.openai.com/settings/organization/billing"
                ) from e
            raise RuntimeError("OpenAI rate limit reached. Wait a moment and try again.") from e
        except APIConnectionError as e:
            raise RuntimeError(
                "Could not connect to OpenAI. Check your internet connection "
                "or set SSL_VERIFY=false in .env on Windows."
            ) from e

    def _demo_response(self, system_prompt: str, user_message: str) -> str:
        role_hint = system_prompt.split(",")[0] if system_prompt else "Agent"
        project_match = re.search(r"Project:\s*(.+)", user_message)
        client_match = re.search(r"Client:\s*(.+)", user_message)
        project = project_match.group(1).strip() if project_match else "New Project"
        client = client_match.group(1).strip() if client_match else "Client"

        if "Marketing" in role_hint or "marketing" in system_prompt.lower()[:80]:
            return (
                f"## Marketing Campaign Results\n\n"
                f"Identified 3 qualified leads for **{project}**:\n"
                f"1. **TechStart Inc.** — Needs e-commerce platform (Budget: $15k–25k)\n"
                f"2. **GreenLeaf Co.** — Needs company website + CMS (Budget: $5k–10k)\n"
                f"3. **{client.split('(')[0].strip()}** — Direct inquiry, high intent\n\n"
                f"Recommended action: Sales team to contact within 24 hours.\n"
                f"Campaign channels: LinkedIn outreach, Google Ads, referral network."
            )

        if "Sales" in role_hint and "requirement" in user_message.lower():
            return (
                f"## Requirements Discovery — {client}\n\n"
                f"**Client Goals:**\n"
                f"- Modern, responsive web application\n"
                f"- User authentication and dashboard\n"
                f"- Admin panel for content management\n"
                f"- Mobile-friendly design\n\n"
                f"**Timeline:** 6–8 weeks\n"
                f"**Budget:** Client indicated flexibility, mid-range budget\n"
                f"**Stakeholders:** {client.split('(')[0].strip()} (Decision Maker)\n\n"
                f"**Next Step:** Forward to Business Analyst for detailed specification."
            )

        if "Sales" in role_hint:
            return (
                f"## Sales Outreach — {project}\n\n"
                f"Contacted **{client}** via email and scheduled discovery call.\n"
                f"Client expressed strong interest in our development services.\n"
                f"Key pain points: outdated systems, need for modern digital presence.\n"
                f"Status: **Qualified Lead** — moving to requirement gathering."
            )

        if "Business Analyst" in role_hint:
            return (
                f"## Business Requirements Document — {project}\n\n"
                f"### Functional Requirements\n"
                f"1. User registration and login (email + OAuth)\n"
                f"2. Dashboard with analytics widgets\n"
                f"3. CRUD operations for main entities\n"
                f"4. Admin panel with role-based access\n"
                f"5. Responsive design (mobile, tablet, desktop)\n\n"
                f"### User Stories\n"
                f"- As a user, I want to sign up so I can access the platform\n"
                f"- As an admin, I want to manage users and content\n"
                f"- As a client, I want real-time data on my dashboard\n\n"
                f"### Recommended Tech Stack\n"
                f"- Frontend: React + Tailwind CSS\n"
                f"- Backend: Python FastAPI\n"
                f"- Database: PostgreSQL\n"
                f"- Hosting: Cloud (AWS/Vercel)"
            )

        if "Finance" in role_hint and "quotation" in user_message.lower():
            return json.dumps(
                {
                    "line_items": [
                        {"item": "Discovery & Requirements", "hours": 20, "rate": 75, "amount": 1500},
                        {"item": "UI/UX Design", "hours": 40, "rate": 80, "amount": 3200},
                        {"item": "Frontend Development", "hours": 80, "rate": 85, "amount": 6800},
                        {"item": "Backend Development", "hours": 80, "rate": 90, "amount": 7200},
                        {"item": "QA & Testing", "hours": 30, "rate": 70, "amount": 2100},
                        {"item": "Deployment & Handover", "hours": 15, "rate": 75, "amount": 1125},
                    ],
                    "notes": "50% upfront, 50% on delivery. Payment to CEO account.",
                },
                indent=2,
            )

        if "Finance" in role_hint:
            valid = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
            return (
                f"## Invoice Generated — {project}\n\n"
                f"**Invoice #INV-{datetime.utcnow().strftime('%Y%m%d')}-001**\n"
                f"**Bill To:** {client}\n"
                f"**Payment Account:** {settings.ceo_name} — Business Account\n"
                f"**Due Date:** {valid}\n\n"
                f"Payment status: Pending client transfer.\n"
                f"Reminder scheduled for 7 days before due date."
            )

        if "HR" in role_hint:
            return (
                f"## Team Assignment — {project}\n\n"
                f"**Recommended Team:**\n"
                f"- Riya Patel (Frontend Developer) — UI components, responsive design\n"
                f"- David Kim (Backend Developer) — APIs, database, authentication\n"
                f"- Elena Vasquez (Full-Stack) — Integration and deployment support\n\n"
                f"All team members are available. Sprint capacity: 2-week sprints.\n"
                f"HR note: Team skills match project requirements."
            )

        if "Project Manager" in role_hint and "review" in user_message.lower():
            return (
                f"## Team Leader Review — {project}\n\n"
                f"**Review Status: APPROVED ✓**\n\n"
                f"**Code Quality:** Meets standards, clean architecture\n"
                f"**Requirements Coverage:** 100% of specified features implemented\n"
                f"**Documentation:** API docs and README complete\n"
                f"**Security:** Authentication and authorization properly implemented\n\n"
                f"Minor notes:\n"
                f"- Consider adding loading states on dashboard (non-blocking)\n"
                f"- Recommend caching for frequently accessed data\n\n"
                f"**Decision:** Approved for QA testing."
            )

        if "Project Manager" in role_hint:
            return (
                f"## Project Kickoff — {project}\n\n"
                f"**Sprint Plan:**\n"
                f"- Sprint 1 (Week 1–2): Setup, auth, core UI\n"
                f"- Sprint 2 (Week 3–4): Dashboard, CRUD features\n"
                f"- Sprint 3 (Week 5–6): Admin panel, integrations\n"
                f"- Sprint 4 (Week 7–8): Polish, testing prep\n\n"
                f"**Assigned Developers:** Riya Patel, David Kim, Elena Vasquez\n"
                f"**Daily standups:** 10 AM | **Demo:** Every Friday"
            )

        if "Frontend" in role_hint:
            return (
                f"## Frontend Deliverables — {project}\n\n"
                f"**Pages Built:**\n"
                f"- Landing page with hero, features, CTA\n"
                f"- Login / Register pages\n"
                f"- User dashboard with charts and data tables\n"
                f"- Admin panel with user management\n\n"
                f"**Tech:** React 18, Tailwind CSS, React Router\n"
                f"**Status:** All components responsive, Lighthouse score 92+"
            )

        if "Backend" in role_hint:
            return (
                f"## Backend Deliverables — {project}\n\n"
                f"**API Endpoints:**\n"
                f"- POST /api/auth/register, /api/auth/login\n"
                f"- GET/POST/PUT/DELETE /api/users\n"
                f"- GET /api/dashboard/stats\n"
                f"- Admin routes with RBAC middleware\n\n"
                f"**Database:** PostgreSQL with migrations\n"
                f"**Security:** JWT auth, input validation, rate limiting"
            )

        if "Full-Stack" in role_hint or "Full-stack" in role_hint:
            return (
                f"## Full-Stack Integration — {project}\n\n"
                f"- Connected frontend to all backend APIs\n"
                f"- Set up CI/CD pipeline (GitHub Actions)\n"
                f"- Docker configuration for local and production\n"
                f"- Environment configs for staging and production\n"
                f"**Deployment:** Ready for cloud deployment"
            )

        if "QA" in role_hint:
            return (
                f"## QA Test Report — {project}\n\n"
                f"**Test Cases Executed:** 47\n"
                f"**Passed:** 45 | **Failed:** 2 (minor UI issues, fixed)\n\n"
                f"**Test Coverage:**\n"
                f"- Authentication flows ✓\n"
                f"- CRUD operations ✓\n"
                f"- Responsive design ✓\n"
                f"- Cross-browser (Chrome, Firefox, Safari) ✓\n"
                f"- API error handling ✓\n\n"
                f"**Bugs Found & Fixed:**\n"
                f"1. [LOW] Button alignment on mobile — Fixed\n"
                f"2. [LOW] Tooltip overflow on small screens — Fixed\n\n"
                f"**Verdict: PASSED — Ready for client handover**"
            )

        if "Client Success" in role_hint:
            return (
                f"## Client Handover Package — {project}\n\n"
                f"**Delivered to {client}:**\n"
                f"1. Source code repository access\n"
                f"2. Deployment guide and credentials\n"
                f"3. User manual (PDF)\n"
                f"4. Admin training session (1 hour, recorded)\n"
                f"5. 30-day post-launch support included\n\n"
                f"**Client Sign-off:** Received — project accepted\n"
                f"**Feedback:** Client satisfied, rated 9/10\n"
                f"**Follow-up:** Support check-in scheduled in 2 weeks"
            )

        return f"## {role_hint} Report\n\nTask completed for **{project}**.\nDetailed output generated successfully."


llm_service = LLMService()
