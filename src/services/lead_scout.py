"""Real-time freelance opportunity discovery from free public platforms."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import httpx

from src.config import settings
from src.services.pricing import outreach_message, tier_summary_for_lead
from src.database.state_store import app_state_store

try:
    import certifi
except ImportError:
    certifi = None

ROOT = Path(__file__).resolve().parent.parent.parent
LEADS_STATE_KEY = "discovered_leads"

# Client needs a freelancer / project-based work
FREELANCE_SIGNALS = re.compile(
    r"\[HIRING\]|\[paid\]|\b(freelance|freelancer|contractor|contract|gig|project-based|"
    r"fixed[- ]price|hourly|one[- ]time|short[- ]term|part[- ]time|consultant|"
    r"need (a |an )?(dev|developer|designer|website|app|help)|"
    r"looking for (a |an )?(dev|developer|freelancer|contractor)|"
    r"build (my |a |an )?(website|app|mvp|product)|"
    r"pay(ing)?\s+\$|budget|bounty|commission)\b",
    re.I,
)

# Full-time employment listings — exclude these
JOB_BLOCKLIST = re.compile(
    r"\[FOR HIRE\]|\b(full[- ]?time|permanent|employee|salary|benefits|401k|w-2|"
    r"who is hiring|years of experience|annual compensation|equity only)\b",
    re.I,
)

DEV_NEED = re.compile(
    r"\b(website|web app|mobile app|e-?commerce|developer|dev|software|mvp|"
    r"landing page|shopify|wordpress|react|node|api)\b",
    re.I,
)

BUDGET_RE = re.compile(
    r"(?:budget|pay(?:ing)?|rate|compensation|offering)\s*:?\s*"
    r"(\$[\d,]+(?:\.\d{2})?(?:\s*[-–]\s*\$[\d,]+)?|\d+\s*(?:k|K)|[\d,]+\s*USD|"
    r"₹[\d,]+(?:\s*(?:k|K|lakhs?))?|INR\s*[\d,]+)"
    r"|(\$[\d,]+(?:\.\d{2})?(?:k|K)?|₹[\d,]+)",
    re.I,
)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
HTTP_HEADERS = {"User-Agent": "AI-Nexus-FreelanceScout/1.0 (CEO dashboard)"}

PLATFORM_ICONS = {
    "reddit": "🔴",
    "hackernews": "🟠",
    "linkedin": "💼",
}

TARGET_REGIONS = ("USA", "UK", "EU", "India", "Japan")

# Block Germany / German-only work
REGION_EXCLUDE = re.compile(
    r"\b(germany|german|deutsch|deutschland|german-speaking|german speaking|"
    r"nur deutsch|berlin|munich|münchen|frankfurt|hamburg|düsseldorf|dusseldorf|"
    r"köln|cologne|stuttgart|leipzig|dresden|hannover|nuremberg|nürnberg|"
    r"\.de\b|@.*\.de\b|dach region|austria-only|österreich)\b",
    re.I,
)

# Explicit non-target countries (when no allowed region also matches)
REGION_BLOCK_OTHER = re.compile(
    r"\b(canada|australian?|australia|brazil|mexico|china|russia|pakistan|"
    r"bangladesh|philippines|nigeria|south africa|uae|dubai|singapore|"
    r"korea|south korea|vietnam|indonesia|turkey|egypt)\b",
    re.I,
)

REGION_USA = re.compile(
    r"\b(usa|u\.?s\.?a?\.?|united states|america|american|usd|dollar|"
    r"new york|san francisco|california|texas|florida|pst|est|cst|mst|remote us)\b",
    re.I,
)
REGION_UK = re.compile(
    r"\b(uk|u\.?k\.?|united kingdom|britain|british|england|scotland|wales|"
    r"london|manchester|gbp|£|remote uk)\b",
    re.I,
)
REGION_INDIA = re.compile(
    r"\b(india|indian|bangalore|bengaluru|mumbai|delhi|hyderabad|pune|chennai|"
    r"kolkata|gurgaon|noida|inr|₹|rupees?|lakhs?)\b",
    re.I,
)
REGION_JAPAN = re.compile(
    r"\b(japan|japanese|tokyo|osaka|kyoto|yokohama|jpy|¥|yen)\b",
    re.I,
)
REGION_EU = re.compile(
    r"\b(eu\b|europe|european|france|french|paris|netherlands|dutch|amsterdam|"
    r"spain|spanish|madrid|barcelona|italy|italian|rome|milan|poland|polish|"
    r"warsaw|portugal|lisbon|ireland|irish|dublin|belgium|sweden|stockholm|"
    r"norway|denmark|finland|euro|€|remote eu|eastern europe)\b",
    re.I,
)
REMOTE_GLOBAL = re.compile(
    r"\b(remote|worldwide|anywhere|global|timezone.?flexible|work from anywhere)\b",
    re.I,
)

REDDIT_FREELANCE_SUBS = [
    ("forhire", "USA/UK/Global clients"),
    ("freelance", "Freelance projects"),
    ("DevPaidProjects", "Paid dev projects"),
    ("INAT", "Paid builds"),
    ("smallbusiness", "SMB projects"),
    ("IndiaBusiness", "India business projects"),
    ("LondonJobs", "UK freelance & contract"),
    ("entrepreneur", "Founders seeking contractors"),
]

JOB_BOARD_SOURCES = frozenset({"remoteok", "jobicy", "arbeitnow"})


class LeadScout:
    def __init__(self) -> None:
        self._leads: dict[str, dict] = {}
        self._scanning = False
        self._last_scan_at: Optional[str] = None
        self._last_scan_sources: list[str] = []
        self._last_error: Optional[str] = None
        self._load()

    def _load(self) -> None:
        try:
            data = app_state_store.get(LEADS_STATE_KEY)
            if not data:
                return
            for lead in data.get("leads", []):
                self._leads[lead["id"]] = lead
            self._last_scan_at = data.get("last_scan_at")
        except (TypeError, KeyError):
            pass

    def _save(self) -> None:
        app_state_store.set(
            LEADS_STATE_KEY,
            {"last_scan_at": self._last_scan_at, "leads": list(self._leads.values())},
        )

    def _classify_region(self, text: str) -> Optional[str]:
        """Return target region label, or None if blocked (e.g. Germany)."""
        if REGION_EXCLUDE.search(text):
            return None

        matched: list[str] = []
        if REGION_USA.search(text):
            matched.append("USA")
        if REGION_UK.search(text):
            matched.append("UK")
        if REGION_EU.search(text):
            matched.append("EU")
        if REGION_INDIA.search(text):
            matched.append("India")
        if REGION_JAPAN.search(text):
            matched.append("Japan")

        if matched:
            return " · ".join(dict.fromkeys(matched))

        if REGION_BLOCK_OTHER.search(text):
            return None

        if REMOTE_GLOBAL.search(text):
            return "Remote · USA/UK/EU/IN/JP"

        # English posts on global boards with no location — allow for target markets
        return "Remote · USA/UK/EU/IN/JP"

    def _is_freelance_lead(self, lead: dict) -> bool:
        if lead.get("opportunity_type") == "job":
            return False
        if lead.get("source") in JOB_BOARD_SOURCES:
            return False
        if lead.get("source") not in ("reddit", "hackernews", "linkedin"):
            return False
        region = lead.get("region")
        if not region:
            region = self._classify_region(
                f"{lead.get('title', '')} {lead.get('description', '')} {lead.get('location', '')}"
            )
        return region is not None

    def get_status(self) -> dict:
        active = [l for l in self._leads.values() if l.get("status") == "new" and self._is_freelance_lead(l)]
        return {
            "enabled": settings.lead_scout_enabled,
            "mode": "freelance",
            "target_regions": list(TARGET_REGIONS),
            "excluded_regions": ["Germany"],
            "scanning": self._scanning,
            "auto_scan_interval_sec": settings.lead_scan_interval_sec,
            "last_scan_at": self._last_scan_at,
            "last_scan_sources": self._last_scan_sources,
            "last_error": self._last_error,
            "total_leads": len([l for l in self._leads.values() if self._is_freelance_lead(l)]),
            "new_leads": len(active),
            "sources": [
                {"id": "reddit", "label": "Reddit · USA, UK, EU, India, Japan gigs", "icon": "🔴"},
                {"id": "hackernews", "label": "Hacker News · US/EU/IN freelance", "icon": "🟠"},
                {"id": "linkedin", "label": "LinkedIn · region-targeted search", "icon": "💼"},
            ],
        }

    def list_leads(self, status: Optional[str] = None, limit: int = 50) -> list[dict]:
        leads = [l for l in self._leads.values() if self._is_freelance_lead(l)]
        if status:
            leads = [l for l in leads if l.get("status") == status]
        leads.sort(key=lambda x: (x.get("score", 0), x.get("discovered_at", "")), reverse=True)
        enriched: list[dict] = []
        for lead in leads[:limit]:
            item = dict(lead)
            if not item.get("region"):
                item["region"] = self._classify_region(
                    f"{item.get('title', '')} {item.get('description', '')}"
                ) or "Remote · USA/UK/EU/IN/JP"
            enriched.append(item)
        return enriched

    def get_lead(self, lead_id: str) -> Optional[dict]:
        lead = self._leads.get(lead_id)
        if lead and self._is_freelance_lead(lead):
            return lead
        return None

    def dismiss_lead(self, lead_id: str) -> bool:
        lead = self._leads.get(lead_id)
        if not lead:
            return False
        lead["status"] = "dismissed"
        self._save()
        return True

    def mark_converted(self, lead_id: str, project_id: int) -> None:
        lead = self._leads.get(lead_id)
        if lead:
            lead["status"] = "converted"
            lead["project_id"] = project_id
            self._save()

    def _http_verify(self):
        if settings.ssl_verify:
            return certifi.where() if certifi else True
        return False

    async def scan(self) -> dict:
        if self._scanning:
            return {"message": "Scan already in progress", **self.get_status()}
        self._scanning = True
        self._last_error = None
        found: list[dict] = []
        sources_ok: list[str] = []
        try:
            async with httpx.AsyncClient(
                timeout=20.0,
                headers=HTTP_HEADERS,
                follow_redirects=True,
                verify=self._http_verify(),
            ) as client:
                fetchers = [
                    ("reddit", self._fetch_reddit(client)),
                    ("hackernews", self._fetch_hackernews(client)),
                    ("linkedin", self._fetch_linkedin_freelance(client)),
                ]
                for name, coro in fetchers:
                    try:
                        batch = await coro
                        if batch:
                            found.extend(batch)
                            sources_ok.append(name)
                    except Exception as exc:
                        self._last_error = f"{name}: {exc}"

            new_count = 0
            for lead in found:
                if lead["id"] not in self._leads:
                    new_count += 1
                self._leads[lead["id"]] = lead

            self._last_scan_at = datetime.utcnow().isoformat()
            self._last_scan_sources = sources_ok
            self._save()
            return {
                "message": (
                    f"Found {new_count} new freelance opportunity(s) "
                    f"from {len(sources_ok)} platform(s)"
                ),
                "new_count": new_count,
                "sources": sources_ok,
                **self.get_status(),
            }
        finally:
            self._scanning = False

    def _lead_id(self, source: str, external_id: str) -> str:
        return hashlib.sha256(f"{source}:{external_id}".encode()).hexdigest()[:16]

    def _is_freelance_opportunity(self, title: str, body: str = "") -> bool:
        text = f"{title} {body}"
        if JOB_BLOCKLIST.search(text):
            return False
        if re.search(r"\[FOR HIRE\]", title, re.I):
            return False
        if FREELANCE_SIGNALS.search(text) and DEV_NEED.search(text):
            return True
        if re.search(r"\[HIRING\]", title, re.I) and DEV_NEED.search(text):
            return True
        if re.search(r"\b(paid|budget|\$\d)", text, re.I) and DEV_NEED.search(text):
            return True
        return False

    def _extract_budget(self, text: str) -> str:
        match = BUDGET_RE.search(text or "")
        if match:
            return (match.group(1) or match.group(2) or "").strip()
        return ""

    def _extract_email(self, text: str) -> str:
        match = EMAIL_RE.search(text or "")
        return match.group(0) if match else ""

    def _guess_company(self, title: str, body: str = "") -> str:
        for text in (title, body):
            m = re.search(r"\[HIRING\]\s*(.+?)(?:\s*[-–|:]|$)", text, re.I)
            if m:
                return m.group(1).strip()[:80]
            m = re.search(r"\[PAID\]\s*(.+?)(?:\s*[-–|:]|$)", text, re.I)
            if m:
                return m.group(1).strip()[:80]
        cleaned = re.sub(r"\[.*?\]", "", title).strip()
        if " — " in cleaned:
            return cleaned.split(" — ")[0].strip()[:80]
        return cleaned[:80] or "Freelance Client"

    def _guess_contact(self, text: str) -> str:
        m = re.search(
            r"(?:contact|reach|dm|email|message)\s*(?:me)?\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            text,
            re.I,
        )
        return m.group(1).strip() if m else "Client"

    def _linkedin_freelance_search(self, keywords: str) -> str:
        return (
            "https://www.linkedin.com/search/results/content/"
            f"?keywords={quote_plus(keywords)}"
        )

    def _linkedin_people_search(self, company: str) -> str:
        q = quote_plus(f"founder {company}")
        return f"https://www.linkedin.com/search/results/people/?keywords={q}"

    def _score_freelance(self, title: str, body: str, budget: str, email: str) -> int:
        text = f"{title} {body}"
        score = 35
        if re.search(r"\[HIRING\]", title, re.I):
            score += 20
        if budget:
            score += 18
        if re.search(r"\b(freelance|contract|fixed|hourly|budget|\$\d)", text, re.I):
            score += 12
        if email and "prospect.mail" not in email:
            score += 15
        if DEV_NEED.search(text):
            score += 10
        return min(100, score)

    def _build_lead(
        self,
        *,
        source: str,
        external_id: str,
        platform_label: str,
        title: str,
        description: str,
        url: str,
        company_name: str = "",
        contact_name: str = "",
        contact_email: str = "",
        budget_hint: str = "",
        location: str = "",
        region: str = "",
        gig_type: str = "Freelance Project",
    ) -> Optional[dict]:
        full_text = f"{title} {description} {location}"
        detected_region = region or self._classify_region(full_text)
        if not detected_region:
            return None

        company = company_name or self._guess_company(title, description)
        contact = contact_name or self._guess_contact(description)
        email = contact_email or self._extract_email(description)
        budget = budget_hint or self._extract_budget(f"{title} {description}")
        if not email:
            slug = re.sub(r"[^a-z0-9]", "", company.lower())[:20] or "client"
            email = f"{slug}@prospect.mail"

        score = self._score_freelance(title, description, budget, email)
        pricing = tier_summary_for_lead(description, title)

        return {
            "id": self._lead_id(source, external_id),
            "source": source,
            "opportunity_type": "freelance",
            "gig_type": gig_type,
            "platform_label": platform_label,
            "platform_icon": PLATFORM_ICONS.get(source, "📌"),
            "title": title[:200],
            "company_name": company,
            "contact_name": contact,
            "contact_email": email,
            "description": description[:2000],
            "budget_hint": budget,
            "location": location or detected_region,
            "region": detected_region,
            "url": url,
            "approach_urls": {
                "original": url,
                "linkedin": self._linkedin_freelance_search(f"{company} freelance developer"),
                "linkedin_people": self._linkedin_people_search(company),
                "reddit": url if source == "reddit" else "",
            },
            "outreach_draft": outreach_message(
                contact,
                title,
                pricing["tier_id"],
                settings.company_name,
            ),
            "pricing_estimate": pricing,
            "score": score,
            "status": "new",
            "project_id": None,
            "discovered_at": datetime.utcnow().isoformat(),
        }

    async def _fetch_reddit(self, client: httpx.AsyncClient) -> list[dict]:
        leads: list[dict] = []
        for sub, label in REDDIT_FREELANCE_SUBS:
            resp = await client.get(
                f"https://www.reddit.com/r/{sub}/new.json",
                params={"limit": 20},
            )
            resp.raise_for_status()
            for child in resp.json().get("data", {}).get("children", []):
                post = child.get("data", {})
                title = post.get("title", "")
                body = post.get("selftext", "") or ""
                if post.get("over_18"):
                    continue
                if not self._is_freelance_opportunity(title, body):
                    continue
                budget = self._extract_budget(f"{title} {body}")
                lead = self._build_lead(
                    source="reddit",
                    external_id=post.get("id", ""),
                    platform_label=f"Reddit · r/{sub} · {label}",
                    title=title,
                    description=body or title,
                    url=f"https://reddit.com{post.get('permalink', '')}",
                    budget_hint=budget,
                    gig_type="Freelance Gig" if sub in ("INAT", "DevPaidProjects") else "Contract Project",
                )
                if lead:
                    leads.append(lead)
        return leads

    async def _fetch_hackernews(self, client: httpx.AsyncClient) -> list[dict]:
        leads: list[dict] = []
        queries = [
            "freelance developer USA project",
            "freelance UK contract website",
            "freelance India developer paid",
            "Japan freelance developer project",
            "Europe freelance contract developer",
        ]
        seen: set[str] = set()
        for q in queries:
            resp = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": q, "tags": "story", "hitsPerPage": 10},
            )
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                title = hit.get("title", "")
                story_id = hit.get("objectID", "")
                if story_id in seen:
                    continue
                if re.search(r"who is hiring", title, re.I):
                    continue
                if not self._is_freelance_opportunity(title, hit.get("story_text") or ""):
                    continue
                seen.add(story_id)
                lead = self._build_lead(
                    source="hackernews",
                    external_id=story_id,
                    platform_label="Hacker News · Freelance / Contract",
                    title=title,
                    description=title,
                    url=f"https://news.ycombinator.com/item?id={story_id}",
                    gig_type="Contract / Freelance",
                )
                if lead:
                    leads.append(lead)
        return leads

    async def _fetch_linkedin_freelance(self, client: httpx.AsyncClient) -> list[dict]:
        """Region-targeted LinkedIn freelance search entry points."""
        queries = [
            ("freelance web developer USA remote", "USA", "USA freelance"),
            ("freelance developer UK contract project", "UK", "UK contract"),
            ("freelance developer Europe EU contract", "EU", "EU freelance"),
            ("hire freelance developer India startup", "India", "India projects"),
            ("freelance web developer Japan 日本", "Japan", "Japan freelance"),
        ]
        leads: list[dict] = []
        for idx, (query, region, gig_type) in enumerate(queries):
            lead = self._build_lead(
                source="linkedin",
                external_id=f"search-{region}-{idx}",
                platform_label=f"LinkedIn · {region} freelance search",
                title=f"{region} freelance opportunity: {gig_type}",
                description=(
                    f"LinkedIn search for {region} clients posting freelance/contract dev work: "
                    f"\"{query}\". Filter by Recent posts. Germany excluded."
                ),
                url=self._linkedin_freelance_search(query),
                company_name=f"{region} prospects",
                region=region,
                gig_type=gig_type,
                budget_hint="Varies — check post",
            )
            if lead:
                leads.append(lead)
        return leads


lead_scout = LeadScout()
