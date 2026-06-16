"""Structured requirement extraction from client text."""

from __future__ import annotations

import re
from typing import Optional

REQUIREMENT_SECTIONS = [
    ("business_goal", "Business goal", r"(?:goal|objective|purpose|about)"),
    ("pages_features", "Pages & features", r"(?:page|feature|section|screen|module)"),
    ("design", "Design & branding", r"(?:design|brand|logo|color|ui|ux|look)"),
    ("integrations", "Integrations", r"(?:integrat|api|stripe|paypal|payment|crm|email)"),
    ("content", "Content", r"(?:content|copy|text|image|photo|video)"),
    ("timeline", "Timeline", r"(?:timeline|deadline|asap|week|month|urgent)"),
    ("budget", "Budget", r"(?:budget|\$\d|usd|price|cost)"),
]


def extract_client_brief(description: str, title: str = "") -> dict:
    text = (description or "").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    brief = {
        "summary": text[:500],
        "raw_description": text,
        "checklist": [],
        "open_questions": [],
    }

    for key, label, pattern in REQUIREMENT_SECTIONS:
        if re.search(pattern, text, re.I):
            brief["checklist"].append({"id": key, "label": label, "status": "mentioned"})
        else:
            brief["open_questions"].append(f"Please confirm: {label}")

    page_match = re.search(r"(\d+)\s*(?:page|pages)", text, re.I)
    if page_match:
        brief["page_count"] = int(page_match.group(1))
    else:
        brief["page_count"] = None

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    if email_match:
        brief["contact_email_found"] = email_match.group(0)

    phone_match = re.search(r"\+?[\d\s\-().]{10,}", text)
    if phone_match:
        brief["contact_phone_found"] = phone_match.group(0).strip()

    if title:
        brief["project_title_hint"] = title

    return brief


def format_requirements_document(
    project_title: str,
    client_name: str,
    description: str,
    agent_analysis: str = "",
    tier_label: str = "",
) -> str:
    brief = extract_client_brief(description, project_title)
    lines = [
        f"# Requirements — {project_title}",
        f"**Client:** {client_name}",
        "",
        "## Client-provided brief",
        description or "_No description provided._",
        "",
        "## Structured checklist",
    ]
    for item in brief["checklist"]:
        lines.append(f"- [x] {item['label']} — mentioned in brief")
    for q in brief["open_questions"][:6]:
        lines.append(f"- [ ] {q}")

    if tier_label:
        lines.extend(["", f"## Recommended service tier", f"**{tier_label}** (USD pricing applied at quotation stage)"])

    if agent_analysis:
        lines.extend(["", "## Team analysis", agent_analysis])

    lines.append("")
    lines.append("## Acceptance criteria")
    lines.append("- Deliverables match the agreed tier scope and client brief above.")
    lines.append("- Client sign-off on staging before final handover.")
    lines.append("- One revision round included unless otherwise quoted.")

    return "\n".join(lines)
