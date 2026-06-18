"""USD pricing tiers and automated quotation for client projects."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.models.schemas import Project, Quotation

TAX_PERCENT = 0.0  # Quotes shown as clean USD totals for clients


@dataclass(frozen=True)
class PricingTier:
    id: str
    label: str
    base_usd: float
    description: str
    delivery_days: str
    includes: list[str]


PRICING_TIERS: dict[str, PricingTier] = {
    "single_page": PricingTier(
        id="single_page",
        label="Single Page Website",
        base_usd=250.0,
        description="One-page landing or brochure site — hero, about, contact, mobile-friendly.",
        delivery_days="3–5 business days",
        includes=[
            "1 responsive page",
            "Contact form or CTA section",
            "Basic SEO meta tags",
            "1 round of revisions",
        ],
    ),
    "dynamic_2_page": PricingTier(
        id="dynamic_2_page",
        label="Dynamic 2-Page Website",
        base_usd=400.0,
        description="Two connected pages with light dynamic content (e.g. home + services or blog list).",
        delivery_days="5–7 business days",
        includes=[
            "2 responsive pages",
            "Simple CMS or editable sections",
            "Contact form + basic analytics hook",
            "2 rounds of revisions",
        ],
    ),
    "ecommerce_starter": PricingTier(
        id="ecommerce_starter",
        label="E-Commerce Starter",
        base_usd=1200.0,
        description="Small online store — product catalog, cart, and checkout integration.",
        delivery_days="2–3 weeks",
        includes=[
            "Up to 25 products",
            "Payment gateway setup",
            "Mobile-responsive storefront",
            "Order notification emails",
        ],
    ),
    "web_application": PricingTier(
        id="web_application",
        label="Web Application",
        base_usd=2500.0,
        description="Custom web app with auth, dashboard, and API-backed features.",
        delivery_days="3–5 weeks",
        includes=[
            "User authentication",
            "Admin dashboard",
            "REST API + database",
            "Deployment guide",
        ],
    ),
    "custom_software": PricingTier(
        id="custom_software",
        label="Fully Custom Software",
        base_usd=4500.0,
        description="End-to-end custom software — multiple modules, integrations, and QA.",
        delivery_days="6–10 weeks",
        includes=[
            "Requirements workshop + BRD",
            "Full-stack development",
            "QA testing pass",
            "Handover documentation",
        ],
    ),
    "mobile_app": PricingTier(
        id="mobile_app",
        label="Mobile App",
        base_usd=3500.0,
        description="Cross-platform mobile app (React Native) with backend API.",
        delivery_days="5–8 weeks",
        includes=[
            "iOS + Android build",
            "Backend API",
            "Push notifications (basic)",
            "App store submission guide",
        ],
    ),
    "social_media_starter": PricingTier(
        id="social_media_starter",
        label="Social Media Starter",
        base_usd=450.0,
        description="Monthly social package — posts, 1 ad set, and 1 reel with client approval workflow.",
        delivery_days="1–2 weeks per batch",
        includes=[
            "4 feed posts + captions",
            "2 paid ad creatives",
            "1 short-form reel script & storyboard",
            "Client review before publish",
            "Upload to Instagram & Facebook",
        ],
    ),
    "social_media_growth": PricingTier(
        id="social_media_growth",
        label="Social Media Growth",
        base_usd=850.0,
        description="Expanded campaign — more posts, ads, reels, and analytics reporting.",
        delivery_days="2–3 weeks per batch",
        includes=[
            "8 posts + content calendar",
            "4 ad variations",
            "2 reels with hooks & scripts",
            "Hashtag & audience strategy",
            "Client approval + scheduled publishing",
        ],
    ),
    "social_media_premium": PricingTier(
        id="social_media_premium",
        label="Social Media Premium",
        base_usd=1500.0,
        description="Full-service social — strategy, design, ads, reels, and multi-platform management.",
        delivery_days="3–4 weeks per batch",
        includes=[
            "12 posts across platforms",
            "6 ad creatives + targeting brief",
            "4 reels (scripts + visual direction)",
            "Monthly analytics report",
            "LinkedIn + Instagram + Facebook publishing",
        ],
    ),
}

TIER_ALIASES = {
    "website": "single_page",
    "landing": "single_page",
    "single": "single_page",
    "single_page": "single_page",
    "2_page": "dynamic_2_page",
    "two_page": "dynamic_2_page",
    "dynamic_2_page": "dynamic_2_page",
    "webapp": "web_application",
    "web_app": "web_application",
    "web_application": "web_application",
    "ecommerce": "ecommerce_starter",
    "ecommerce_starter": "ecommerce_starter",
    "custom": "custom_software",
    "custom_software": "custom_software",
    "mobile": "mobile_app",
    "mobile_app": "mobile_app",
    "social_media": "social_media_starter",
    "social": "social_media_starter",
    "social_media_starter": "social_media_starter",
    "social_media_growth": "social_media_growth",
    "social_media_premium": "social_media_premium",
}


def list_tiers() -> list[dict]:
    return [
        {
            "id": t.id,
            "label": t.label,
            "base_usd": t.base_usd,
            "description": t.description,
            "delivery_days": t.delivery_days,
            "includes": t.includes,
        }
        for t in PRICING_TIERS.values()
    ]


def get_tier(tier_id: str) -> Optional[PricingTier]:
    key = TIER_ALIASES.get(tier_id.lower().strip(), tier_id.lower().strip())
    return PRICING_TIERS.get(key)


def parse_budget_range(text: str) -> tuple[Optional[float], Optional[float]]:
    """Parse client budget hints like '$500 - $1,500' or 'Under $500'."""
    blob = text or ""
    range_match = re.search(
        r"(?:budget[:\s]*)?\$?\s*([\d,]+)\s*[-–]\s*\$?\s*([\d,]+)",
        blob,
        re.I,
    )
    if range_match:
        low = float(range_match.group(1).replace(",", ""))
        high = float(range_match.group(2).replace(",", ""))
        return low, high

    under_match = re.search(r"under\s*\$?\s*([\d,]+)", blob, re.I)
    if under_match:
        high = float(under_match.group(1).replace(",", ""))
        return None, high

    single_match = re.search(r"(?:budget[:\s]*)\$?\s*([\d,]+)", blob, re.I)
    if single_match:
        val = float(single_match.group(1).replace(",", ""))
        return val, val

    return None, None


def classify_tier(
    text: str,
    project_type: str = "",
    explicit_tier: str = "",
) -> str:
    if explicit_tier:
        tier = get_tier(explicit_tier)
        if tier:
            return tier.id

    if project_type:
        mapped = TIER_ALIASES.get(project_type.lower().strip())
        if mapped:
            base_tier = mapped
        else:
            base_tier = ""
    else:
        base_tier = ""

    blob = (text or "").lower()

    if project_type in ("social_media", "social"):
        inferred = "social_media_starter"
    elif re.search(r"\b(social media|instagram|facebook ads|reels?|tiktok|content calendar|graphic design)\b", blob):
        if re.search(r"\b(premium|full service|12 post|monthly management)\b", blob):
            inferred = "social_media_premium"
        elif re.search(r"\b(growth|8 post|analytics)\b", blob):
            inferred = "social_media_growth"
        else:
            inferred = "social_media_starter"
    elif re.search(r"\b(mobile app|react native|ios|android|expo)\b", blob):
        inferred = "mobile_app"
    elif re.search(r"\b(custom software|erp|crm|saas platform|enterprise)\b", blob):
        inferred = "custom_software"
    elif re.search(r"\b(web app|webapp|dashboard|portal|saas)\b", blob):
        inferred = "web_application"
    elif re.search(r"\b(e-?commerce|shopify|woocommerce|online store|cart)\b", blob):
        inferred = "ecommerce_starter"
    elif re.search(
        r"\b(carousel|slider|about us|contact form|multiple pages|2[\s-]?page|two page|multi[\s-]?page)\b",
        blob,
    ):
        inferred = "dynamic_2_page"
    elif re.search(r"\b(single page|landing page|one page|brochure|normal website|simple website)\b", blob):
        inferred = "single_page"
    elif base_tier:
        inferred = base_tier
    elif project_type in ("webapp",):
        inferred = "web_application"
    elif project_type in ("ecommerce",):
        inferred = "ecommerce_starter"
    elif project_type in ("mobile",):
        inferred = "mobile_app"
    elif project_type in ("custom",):
        inferred = "custom_software"
    else:
        inferred = "single_page"

    return resolve_tier_for_budget(inferred, text)


def resolve_tier_for_budget(tier_id: str, text: str) -> str:
    """Pick the best tier that fits the client's stated budget (never exceed max)."""
    _, max_budget = parse_budget_range(text)
    tier = get_tier(tier_id) or PRICING_TIERS["single_page"]

    if not max_budget:
        return tier.id

    if tier.base_usd <= max_budget:
        return tier.id

    affordable = sorted(
        [t for t in PRICING_TIERS.values() if t.base_usd <= max_budget],
        key=lambda t: t.base_usd,
        reverse=True,
    )
    if affordable:
        return affordable[0].id

    return "single_page"


def estimate_adjustments(text: str, tier_id: str) -> list[dict]:
    """Small add-ons when requirements clearly exceed the base tier."""
    blob = (text or "").lower()
    extras: list[dict] = []

    def add(item: str, amount: float) -> None:
        extras.append({"item": item, "hours": 0, "rate": 0, "amount": amount})

    if re.search(r"\b(payment|stripe|paypal|checkout)\b", blob) and tier_id in (
        "single_page",
        "dynamic_2_page",
    ):
        add("Payment integration add-on", 150.0)
    if re.search(r"\b(admin panel|cms|content management)\b", blob) and tier_id == "single_page":
        add("Admin/CMS add-on", 200.0)
    if re.search(r"\b(api integration|third[\s-]?party|webhook)\b", blob):
        add("API integration", 250.0)
    if re.search(r"\b(multilingual|i18n|translation)\b", blob):
        add("Multi-language support", 180.0)
    if re.search(r"\b(urgent|rush|asap|48 hours)\b", blob):
        add("Rush delivery", 100.0)

    return extras


def build_quotation(
    project_id: int,
    project: Project,
    tier_id: Optional[str] = None,
    llm_line_items: Optional[list[dict]] = None,
) -> Quotation:
    blob = f"{project.title} {project.description} {project.requirements}"
    resolved = tier_id or classify_tier(
        blob,
        explicit_tier=getattr(project, "pricing_tier", "") or "",
    )
    resolved = resolve_tier_for_budget(resolved, blob)
    tier = get_tier(resolved) or PRICING_TIERS["single_page"]

    line_items: list[dict] = [
        {
            "item": tier.label,
            "description": tier.description,
            "hours": "-",
            "rate": "Fixed",
            "amount": tier.base_usd,
        }
    ]

    for extra in estimate_adjustments(blob, tier.id):
        line_items.append({
            "item": extra["item"],
            "hours": "-",
            "rate": "Fixed",
            "amount": extra["amount"],
        })

    subtotal = round(sum(float(i.get("amount", 0) or 0) for i in line_items), 2)

    _, max_budget = parse_budget_range(blob)
    if max_budget and subtotal > max_budget:
        line_items = [{
            "item": tier.label,
            "description": f"Scoped to client budget (max ${max_budget:,.0f} USD)",
            "hours": "-",
            "rate": "Fixed",
            "amount": min(tier.base_usd, max_budget),
        }]
        subtotal = line_items[0]["amount"]

    tax_amount = round(subtotal * TAX_PERCENT / 100, 2)
    total = round(subtotal + tax_amount, 2)
    valid = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

    budget_note = ""
    _, max_b = parse_budget_range(blob)
    if max_b:
        budget_note = f" Client budget: up to ${max_b:,.0f} USD."

    notes = (
        f"Fixed package: {tier.label} · Delivery: {tier.delivery_days}.{budget_note} "
        f"All prices in USD. 50% upfront, 50% on delivery."
    )

    return Quotation(
        project_id=project_id,
        line_items=line_items,
        subtotal=subtotal,
        tax_percent=TAX_PERCENT,
        tax_amount=tax_amount,
        total_amount=total,
        currency="USD",
        valid_until=valid,
        notes=notes,
    )


def outreach_message(
    contact_name: str,
    post_title: str,
    tier_id: str,
    company_name: str,
) -> str:
    tier = get_tier(tier_id) or PRICING_TIERS["single_page"]
    first = (contact_name or "there").split()[0]
    return (
        f"Hi {first},\n\n"
        f"I saw your post \"{post_title[:80]}\" — we at {company_name} deliver quality work "
        f"at lean rates because our AI-assisted team moves fast.\n\n"
        f"For projects like yours, we typically quote from ${tier.base_usd:,.0f} USD "
        f"({tier.label}) depending on exact scope. That includes:\n"
        + "".join(f"  • {item}\n" for item in tier.includes[:3])
        + f"\nWe can share a fixed quote within 24 hours once we confirm requirements. "
        f"Would a quick 15-min call work to clarify scope?\n\n"
        f"Best regards"
    )


def tier_summary_for_lead(description: str, title: str = "") -> dict:
    tier_id = classify_tier(f"{title} {description}")
    tier = get_tier(tier_id) or PRICING_TIERS["single_page"]
    return {
        "tier_id": tier.id,
        "tier_label": tier.label,
        "estimated_usd": tier.base_usd,
        "delivery_days": tier.delivery_days,
    }
