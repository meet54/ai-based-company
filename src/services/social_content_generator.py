"""Generate social posts, ads, and reel storyboards for client campaigns."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.models.schemas import Project
from src.services.llm import llm_service

ROOT = Path(__file__).resolve().parent.parent.parent
DELIVERABLES_DIR = ROOT / "deliverables"


@dataclass
class SocialPost:
    id: str
    platform: str
    title: str
    caption: str
    hashtags: list[str]
    cta: str
    visual_brief: str
    post_type: str = "feed"


@dataclass
class SocialAd:
    id: str
    platform: str
    headline: str
    body: str
    cta: str
    audience: str
    visual_brief: str


@dataclass
class SocialReel:
    id: str
    platform: str
    title: str
    hook: str
    script: list[str]
    duration_sec: int
    music_mood: str
    hashtags: list[str]
    visual_brief: str


@dataclass
class SocialCampaign:
    client: str
    brand: str
    platforms: list[str]
    posts: list[SocialPost] = field(default_factory=list)
    ads: list[SocialAd] = field(default_factory=list)
    reels: list[SocialReel] = field(default_factory=list)


def _detect_platforms(text: str) -> list[str]:
    blob = (text or "").lower()
    platforms = []
    for name, keys in (
        ("Instagram", ("instagram", "insta", "ig ")),
        ("Facebook", ("facebook", "fb ")),
        ("LinkedIn", ("linkedin",)),
        ("TikTok", ("tiktok", "tik tok")),
    ):
        if any(k in blob for k in keys):
            platforms.append(name)
    return platforms or ["Instagram", "Facebook", "LinkedIn"]


def _brand_name(project: Project) -> str:
    blob = f"{project.title} {project.description} {project.requirements or ''}"
    extracted = _extract_brand_from_text(blob)
    if extracted:
        return extracted
    return project.client_company or project.title.split("—")[0].strip()


def _extract_brand_from_text(text: str) -> str:
    for pat in (
        r"brand\s*(?:name\s*is|:)\s*[\"']?([A-Za-z0-9][\w\s&'-]{0,40})[\"']?",
        r"for\s+(?:the\s+)?brand\s+[\"']?([A-Za-z0-9][\w\s&'-]{0,40})[\"']?",
        r"our\s+brand\s+[\"']?([A-Za-z0-9][\w\s&'-]{0,40})[\"']?",
    ):
        match = re.search(pat, text, re.I)
        if match:
            return _title_brand(match.group(1).strip())
    return ""


def _title_brand(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name).strip()
    if not cleaned:
        return cleaned
    if cleaned.isupper() or cleaned.islower():
        return cleaned.title()
    return cleaned


def _extract_discount_pct(text: str) -> int | None:
    for pat in (
        r"(?:up\s*to|upto)\s*(\d{1,2})\s*%",
        r"(\d{1,2})\s*%\s*(?:off|discount)",
        r"(\d{1,2})\s*%\s+on",
    ):
        match = re.search(pat, text, re.I)
        if match:
            return min(99, max(1, int(match.group(1))))
    return None


def _extract_product_line(text: str) -> str:
    blob = (text or "").lower()
    if re.search(r"\bcloth(?:es|ing)?\b|\bapparel\b|\bfashion\b|\bwear\b|\boutfit", blob):
        return "clothing"
    if re.search(r"\bmenu\b|\bfood\b|\bcaf[eé]\b|\brestaurant\b", blob):
        return "menu items"
    if re.search(r"\bservice\b|\bconsult", blob):
        return "services"
    return "products"


def _is_sale_campaign(text: str) -> bool:
    blob = (text or "").lower()
    return bool(
        re.search(
            r"\b(?:sale|discount|%\s*off|off\s+on|clearance|promo|offer|deal)\b",
            blob,
        )
        or _extract_discount_pct(blob) is not None
    )


def _wants_single_post(text: str) -> bool:
    return bool(re.search(r"\b(?:create|make|need)\s+(?:a\s+)?post\b", text, re.I))


@dataclass
class CampaignBrief:
    brand: str
    client: str
    platforms: list[str]
    is_sale: bool = False
    discount_pct: int | None = None
    product_line: str = "products"
    single_post_focus: bool = False
    raw_summary: str = ""


def _parse_campaign_brief(project: Project) -> CampaignBrief:
    blob = f"{project.title}\n{project.description}\n{project.requirements or ''}"
    brand = _brand_name(project)
    platforms = _detect_platforms(blob)
    discount = _extract_discount_pct(blob)
    product = _extract_product_line(blob)
    is_sale = _is_sale_campaign(blob)
    return CampaignBrief(
        brand=brand,
        client=project.client_name or "Client",
        platforms=platforms,
        is_sale=is_sale or discount is not None,
        discount_pct=discount,
        product_line=product,
        single_post_focus=_wants_single_post(blob),
        raw_summary=(project.description or "")[:300],
    )


def _hashtag(brand: str, *extra: str) -> list[str]:
    tags = [f"#{re.sub(r'[^A-Za-z0-9]', '', brand)}" if brand else "#Brand"]
    tags.extend(f"#{t}" for t in extra)
    return tags


def _sale_campaign(brief: CampaignBrief) -> SocialCampaign:
    brand = brief.brand
    discount = brief.discount_pct or 50
    product = brief.product_line
    platform = "Instagram" if "Instagram" in brief.platforms else brief.platforms[0]
    product_label = "ALL clothing" if product == "clothing" else f"our entire {product}"

    posts = [
        SocialPost(
            id="post-01",
            platform=platform,
            title=f"{discount}% Off Sale — {brand}",
            caption=(
                f"🔥 {brand.upper()} SALE IS LIVE!\n\n"
                f"Up to {discount}% OFF on {product_label}! 👗✨\n\n"
                f"Your favourite styles, now at unbeatable prices. "
                f"Hurry — limited stock on bestsellers.\n\n"
                f"🛍️ Shop via link in bio\n"
                f"📲 Share with someone who loves a good deal!"
            ),
            hashtags=_hashtag(
                brand, "Sale", f"{discount}Off", "FashionSale", "ShopNow", "InstaFashion",
            ),
            cta="Shop the sale",
            visual_brief=(
                f"Instagram feed 1080×1080: bold '{discount}% OFF' typography, {brand} logo, "
                f"clothing flat-lay or model shot, high-contrast sale colors (red/gold on dark)."
            ),
            post_type="feed",
        ),
        SocialPost(
            id="post-02",
            platform=platform,
            title="Carousel — Top picks",
            caption=(
                f"Swipe to see what’s flying off the racks at {brand}! ➡️\n\n"
                f"Every slide = up to {discount}% off.\n"
                f"Which look is your favourite? Comment the slide number! 👇"
            ),
            hashtags=_hashtag(brand, "Carousel", "OOTD", "StyleInspo", "SaleAlert"),
            cta="Swipe & shop",
            visual_brief=(
                f"5-slide carousel: cover '{discount}% OFF', slides 2–5 outfit combos with price badges, "
                f"{brand} branding on each slide."
            ),
            post_type="carousel",
        ),
        SocialPost(
            id="post-03",
            platform=platform,
            title="Last chance reminder",
            caption=(
                f"⏰ Last call — {brand} {discount}% sale ends soon!\n\n"
                f"Don't miss out on {product} at the best prices of the season. "
                f"Tap the link in bio before it's gone."
            ),
            hashtags=_hashtag(brand, "LastChance", "SaleEndsSoon", "FashionDeals"),
            cta="Shop before it ends",
            visual_brief="Urgency graphic: countdown style, bold CTA, product collage, brand logo footer.",
            post_type="feed",
        ),
    ]

    if brief.single_post_focus:
        posts = posts[:1]

    ads = [
        SocialAd(
            id="ad-01",
            platform=platform,
            headline=f"Up to {discount}% Off at {brand}",
            body=(
                f"Shop {brand} {product} at up to {discount}% off. "
                "Limited-time offer — tap to shop the full sale collection."
            ),
            cta="Shop now",
            audience=f"Fashion shoppers 18–40, interest in {product}, online buyers",
            visual_brief=(
                f"Paid ad: hero product image, '{discount}% OFF' badge, {brand} logo, "
                "Shop Now button, mobile-first layout."
            ),
        ),
    ]

    reels = [
        SocialReel(
            id="reel-01",
            platform=platform,
            title=f"{discount}% sale announcement",
            hook=f"{brand} — up to {discount}% off EVERYTHING. Watch before it ends 👀",
            script=[
                f"Hook text on screen: '{discount}% OFF' + {brand} logo (0–3s)",
                "Quick cuts: 3–4 bestselling outfits with price overlays (3–12s)",
                f"Text: 'All {product} included' + swipe-up arrow (12–18s)",
                f"CTA end card: 'Shop {brand} — link in bio' (18–25s)",
            ],
            duration_sec=25,
            music_mood="Trendy upbeat pop / fashion reel audio",
            hashtags=_hashtag(brand, "Reels", "FashionSale", "OOTD", f"{discount}Off"),
            visual_brief="Vertical 9:16, fast transitions, bold captions, brand color accents.",
        ),
    ]

    return SocialCampaign(
        client=brief.client,
        brand=brand,
        platforms=brief.platforms,
        posts=posts,
        ads=ads,
        reels=reels if not brief.single_post_focus else reels[:1],
    )


def _default_campaign(project: Project) -> SocialCampaign:
    brief = _parse_campaign_brief(project)
    if brief.is_sale:
        return _sale_campaign(brief)

    brand = brief.brand
    client = brief.client
    platforms = brief.platforms
    topic = project.title.replace(f"{brand} —", "").strip() or "your brand"

    posts = [
        SocialPost(
            id="post-01",
            platform=platforms[0],
            title="Brand introduction",
            caption=(
                f"Meet {brand} — built for people who want more from every day. "
                f"We're here to help you {topic[:60]}. Tap follow for tips, updates, and behind-the-scenes."
            ),
            hashtags=["#BrandStory", "#SmallBusiness", "#Growth", f"#{brand.replace(' ', '')}"],
            cta="Follow us",
            visual_brief=f"Clean hero visual with {brand} logo, warm gradient background, product/service highlight.",
            post_type="feed",
        ),
        SocialPost(
            id="post-02",
            platform=platforms[0],
            title="Value tip carousel",
            caption=(
                "3 quick wins you can try today:\n"
                "1️⃣ Start with one clear goal\n"
                "2️⃣ Show real results — not jargon\n"
                "3️⃣ Engage within the first hour\n\n"
                f"Save this post & share with your team. {brand} is rooting for you."
            ),
            hashtags=["#Tips", "#Marketing", "#Carousel", "#SaveThis"],
            cta="Save & share",
            visual_brief="Carousel slide design — bold numbers, icon per slide, brand colors.",
            post_type="carousel",
        ),
        SocialPost(
            id="post-03",
            platform=platforms[-1] if len(platforms) > 1 else platforms[0],
            title="Client success spotlight",
            caption=(
                f"Results speak louder than promises. Here's how teams like yours use {brand} "
                "to save time and grow faster. Want the full playbook? Comment 'GUIDE' below."
            ),
            hashtags=["#CaseStudy", "#Results", "#B2B" if "LinkedIn" in platforms else "#Success"],
            cta="Comment GUIDE",
            visual_brief="Before/after stat layout, testimonial quote bubble, professional photo style.",
            post_type="feed",
        ),
        SocialPost(
            id="post-04",
            platform=platforms[0],
            title="Weekend engagement",
            caption=(
                f"Happy weekend from the {brand} team! What's one win you're celebrating this week? "
                "Drop it in the comments — we read every one."
            ),
            hashtags=["#Community", "#WeekendVibes", "#Engagement"],
            cta="Comment below",
            visual_brief="Lifestyle candid team/office shot, soft natural lighting, friendly mood.",
            post_type="feed",
        ),
    ]

    ads = [
        SocialAd(
            id="ad-01",
            platform=platforms[0],
            headline=f"Grow with {brand}",
            body=(
                f"Reach the right audience with campaigns crafted for {topic[:50]}. "
                "Limited-time onboarding — book a free strategy call."
            ),
            cta="Book free call",
            audience="Business owners & decision makers, 25–45, interest in growth",
            visual_brief="Split layout: headline left, product mockup right, high-contrast CTA button.",
        ),
        SocialAd(
            id="ad-02",
            platform="Facebook" if "Facebook" in platforms else platforms[0],
            headline="See it in action",
            body=(
                f"Watch how {brand} helps you launch faster. "
                "Social-ready creatives + copy included. Start this week."
            ),
            cta="Get started",
            audience="Lookalike — website visitors, retargeting 7 days",
            visual_brief="Video thumbnail style frame, play button overlay, bold offer badge.",
        ),
    ]

    reels = [
        SocialReel(
            id="reel-01",
            platform="Instagram" if "Instagram" in platforms else platforms[0],
            title="60-second brand story",
            hook=f"Stop scrolling — here's what {brand} actually does in 60 seconds.",
            script=[
                "Hook on screen: bold text + logo sting (0–3s)",
                "Problem: 'Tired of generic content that gets zero engagement?' (3–10s)",
                f"Solution: Show {brand} dashboard / product / service clip (10–25s)",
                "Social proof: quick stat or client quote overlay (25–40s)",
                "CTA: 'Link in bio — free consult' + logo end card (40–60s)",
            ],
            duration_sec=60,
            music_mood="Upbeat corporate pop, 120 BPM",
            hashtags=["#Reels", "#Brand", "#MarketingTips", f"#{brand.replace(' ', '')}"],
            visual_brief="Fast cuts, kinetic typography, brand color accents, vertical 9:16.",
        ),
        SocialReel(
            id="reel-02",
            platform="Instagram" if "Instagram" in platforms else platforms[0],
            title="3 tips in 30 seconds",
            hook="3 social media mistakes costing you leads 👇",
            script=[
                "Text-on-screen mistake #1 with X icon (0–10s)",
                "Mistake #2 — talking head or b-roll (10–20s)",
                "Mistake #3 + fix summary (20–28s)",
                f"End: '{brand} — we fix this for you' + follow CTA (28–30s)",
            ],
            duration_sec=30,
            music_mood="Trending lo-fi beat, subtle",
            hashtags=["#SocialMediaTips", "#ReelsIndia", "#GrowthHacks"],
            visual_brief="Talking-head + screen recordings, large caption subtitles, punchy transitions.",
        ),
    ]

    return SocialCampaign(
        client=client,
        brand=brand,
        platforms=platforms,
        posts=posts,
        ads=ads,
        reels=reels,
    )


def _post_card_html(post: SocialPost, brand: str) -> str:
    tags = " ".join(html.escape(t) for t in post.hashtags)
    return f"""<article class="asset-card post-card platform-{post.platform.lower()}">
  <div class="asset-badge">{html.escape(post.platform)} · {html.escape(post.post_type)}</div>
  <div class="post-visual"><span>{html.escape(post.visual_brief[:120])}</span></div>
  <h3>{html.escape(post.title)}</h3>
  <p class="caption">{html.escape(post.caption)}</p>
  <p class="hashtags">{tags}</p>
  <p class="cta-pill">{html.escape(post.cta)}</p>
</article>"""


def _ad_card_html(ad: SocialAd) -> str:
    return f"""<article class="asset-card ad-card">
  <div class="asset-badge">{html.escape(ad.platform)} · Paid Ad</div>
  <div class="ad-mock">
    <strong>{html.escape(ad.headline)}</strong>
    <p>{html.escape(ad.body)}</p>
    <button type="button">{html.escape(ad.cta)}</button>
  </div>
  <p class="meta"><strong>Audience:</strong> {html.escape(ad.audience)}</p>
  <p class="meta"><strong>Visual:</strong> {html.escape(ad.visual_brief)}</p>
</article>"""


def _reel_card_html(reel: SocialReel) -> str:
    scenes = "".join(f"<li>{html.escape(s)}</li>" for s in reel.script)
    tags = " ".join(html.escape(t) for t in reel.hashtags)
    return f"""<article class="asset-card reel-card">
  <div class="reel-frame">
    <div class="reel-play">▶</div>
    <div class="reel-hook">{html.escape(reel.hook)}</div>
    <div class="reel-duration">{reel.duration_sec}s</div>
  </div>
  <div class="asset-badge">{html.escape(reel.platform)} · Reel</div>
  <h3>{html.escape(reel.title)}</h3>
  <p class="meta"><strong>Music:</strong> {html.escape(reel.music_mood)}</p>
  <ol class="reel-script">{scenes}</ol>
  <p class="hashtags">{tags}</p>
  <p class="meta"><strong>Visual direction:</strong> {html.escape(reel.visual_brief)}</p>
</article>"""


def _gallery_html(campaign: SocialCampaign, project: Project) -> str:
    posts = "\n".join(_post_card_html(p, campaign.brand) for p in campaign.posts)
    ads = "\n".join(_ad_card_html(a) for a in campaign.ads)
    reels = "\n".join(_reel_card_html(r) for r in campaign.reels)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(campaign.brand)} — Social Campaign Preview</title>
  <style>
    :root {{
      --bg: #0f1419; --card: #1a2332; --text: #e8edf5; --muted: #8b9cb3;
      --accent: #6366f1; --ig: #e1306c; --fb: #1877f2; --li: #0a66c2;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, system-ui, sans-serif; background: var(--bg); color: var(--text); }}
    header {{ padding: 2rem; text-align: center; border-bottom: 1px solid #2a3548; }}
    header h1 {{ margin: 0 0 0.5rem; font-size: 1.75rem; }}
    header p {{ color: var(--muted); margin: 0; }}
    .status {{ display: inline-block; margin-top: 1rem; padding: 0.35rem 0.9rem; border-radius: 999px;
      background: rgba(245,158,11,.15); color: #fbbf24; font-size: 0.85rem; }}
    section {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
    h2 {{ font-size: 1.25rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.25rem; }}
    .asset-card {{ background: var(--card); border-radius: 12px; padding: 1rem; border: 1px solid #2a3548; }}
    .asset-badge {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin-bottom: 0.75rem; }}
    .post-visual {{ height: 140px; border-radius: 8px; background: linear-gradient(135deg,#312e81,#4f46e5);
      display: flex; align-items: center; justify-content: center; text-align: center; padding: 1rem;
      font-size: 0.8rem; color: #c7d2fe; margin-bottom: 0.75rem; }}
    .caption {{ white-space: pre-wrap; font-size: 0.9rem; line-height: 1.5; }}
    .hashtags {{ color: var(--accent); font-size: 0.8rem; }}
    .cta-pill {{ display: inline-block; background: var(--accent); color: white; padding: 0.25rem 0.75rem;
      border-radius: 999px; font-size: 0.8rem; margin-top: 0.5rem; }}
    .ad-mock {{ background: #fff; color: #111; border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem; }}
    .ad-mock button {{ background: #1877f2; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 6px; margin-top: 0.5rem; }}
    .meta {{ font-size: 0.8rem; color: var(--muted); }}
    .reel-card {{ grid-column: span 1; }}
    .reel-frame {{ aspect-ratio: 9/16; max-height: 320px; margin: 0 auto 0.75rem; border-radius: 12px;
      background: linear-gradient(180deg,#1e1b4b,#312e81); position: relative; display: flex;
      align-items: flex-end; padding: 1rem; overflow: hidden; }}
    .reel-play {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
      width: 48px; height: 48px; border-radius: 50%; background: rgba(255,255,255,.2);
      display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }}
    .reel-hook {{ font-weight: 600; font-size: 0.95rem; z-index: 1; }}
    .reel-duration {{ position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,.5);
      padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }}
    .reel-script {{ font-size: 0.8rem; color: var(--muted); padding-left: 1.2rem; }}
    .platform-instagram .post-visual {{ background: linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045); }}
    footer {{ text-align: center; padding: 2rem; color: var(--muted); font-size: 0.8rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(campaign.brand)} — Social Media Campaign</h1>
    <p>Prepared for {html.escape(campaign.client)} · Platforms: {html.escape(", ".join(campaign.platforms))}</p>
    <span class="status">⏳ Awaiting client approval before publish</span>
  </header>
  <section>
    <h2>📱 Feed Posts ({len(campaign.posts)})</h2>
    <div class="grid">{posts}</div>
  </section>
  <section>
    <h2>📢 Paid Ads ({len(campaign.ads)})</h2>
    <div class="grid">{ads}</div>
  </section>
  <section>
    <h2>🎬 Reels ({len(campaign.reels)})</h2>
    <div class="grid">{reels}</div>
  </section>
  <footer>Generated by AI Nexus Social Media Team · Project #{project.id}</footer>
</body>
</html>"""


class SocialContentGenerator:
    def social_dir(self, project_id: int) -> Path:
        return DELIVERABLES_DIR / f"project-{project_id}" / "social"

    def has_preview(self, project_id: int) -> bool:
        return (self.social_dir(project_id) / "index.html").is_file()

    def preview_url(self, project_id: int) -> str | None:
        if self.has_preview(project_id):
            return f"/deliverables/{project_id}/social/index.html"
        return None

    def list_files(self, project_id: int) -> list[dict]:
        base = self.social_dir(project_id)
        if not base.exists():
            return []
        files = []
        for path in sorted(base.rglob("*")):
            if path.is_file():
                rel = path.relative_to(self.social_dir(project_id)).as_posix()
                files.append({
                    "path": f"social/{rel}",
                    "size": path.stat().st_size,
                    "extension": path.suffix.lstrip("."),
                })
        return files

    async def generate(self, project: Project, agent_context: str = "") -> dict:
        DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
        out_dir = self.social_dir(project.id)
        out_dir.mkdir(parents=True, exist_ok=True)

        campaign = _default_campaign(project)
        if agent_context:
            campaign = await self._enhance_from_llm(project, campaign, agent_context)

        campaign_dict = {
            "client": campaign.client,
            "brand": campaign.brand,
            "platforms": campaign.platforms,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "pending_client_approval",
            "posts": [p.__dict__ for p in campaign.posts],
            "ads": [a.__dict__ for a in campaign.ads],
            "reels": [r.__dict__ for r in campaign.reels],
        }
        (out_dir / "campaign.json").write_text(
            json.dumps(campaign_dict, indent=2), encoding="utf-8"
        )
        (out_dir / "index.html").write_text(
            _gallery_html(campaign, project), encoding="utf-8"
        )

        files_written = ["social/index.html", "social/campaign.json"]
        for post in campaign.posts:
            path = f"social/posts/{post.id}.json"
            (out_dir / "posts" / f"{post.id}.json").parent.mkdir(parents=True, exist_ok=True)
            (out_dir / "posts" / f"{post.id}.json").write_text(
                json.dumps(post.__dict__, indent=2), encoding="utf-8"
            )
            files_written.append(path)

        for ad in campaign.ads:
            (out_dir / "ads").mkdir(parents=True, exist_ok=True)
            (out_dir / "ads" / f"{ad.id}.json").write_text(
                json.dumps(ad.__dict__, indent=2), encoding="utf-8"
            )
            files_written.append(f"social/ads/{ad.id}.json")

        for reel in campaign.reels:
            (out_dir / "reels").mkdir(parents=True, exist_ok=True)
            (out_dir / "reels" / f"{reel.id}.json").write_text(
                json.dumps(reel.__dict__, indent=2), encoding="utf-8"
            )
            files_written.append(f"social/reels/{reel.id}.json")

        return {
            "directory": str(out_dir),
            "files_written": files_written,
            "file_count": len(files_written),
            "platforms": campaign.platforms,
            "post_count": len(campaign.posts),
            "ad_count": len(campaign.ads),
            "reel_count": len(campaign.reels),
        }

    async def _enhance_from_llm(
        self, project: Project, campaign: SocialCampaign, context: str
    ) -> SocialCampaign:
        brief = _parse_campaign_brief(project)
        prompt = (
            f"Client brand: {campaign.brand}\n"
            f"Platforms: {', '.join(campaign.platforms)}\n"
            f"Client brief:\n{project.description}\n\n"
            f"Team context:\n{context[:1200]}\n\n"
            "Rewrite post-01 caption for Instagram (max 300 chars). "
            "Use the client's offer, brand name, and CTA. Return caption text only."
        )
        try:
            text = await llm_service.complete(
                "You are a social media copywriter for fashion and retail brands.", prompt
            )
            if text and len(text) < 500:
                campaign.posts[0].caption = text.strip().strip('"')
        except Exception:
            pass
        if brief.is_sale and campaign.posts:
            discount = brief.discount_pct or 50
            campaign.posts[0].title = f"{discount}% Off Sale — {campaign.brand}"
        return campaign

    def mark_published(self, project_id: int, platforms: list[str]) -> None:
        json_path = self.social_dir(project_id) / "campaign.json"
        if not json_path.is_file():
            return
        data = json.loads(json_path.read_text(encoding="utf-8"))
        data["status"] = "published"
        data["published_at"] = datetime.utcnow().isoformat()
        data["published_platforms"] = platforms
        json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        html_path = self.social_dir(project_id) / "index.html"
        if html_path.is_file():
            content = html_path.read_text(encoding="utf-8")
            content = content.replace(
                "Awaiting client approval before publish",
                f"Published to {', '.join(platforms)}",
            )
            content = re.sub(
                r'class="status"[^>]*>[^<]+</span>',
                f'class="status" style="background:rgba(16,185,129,.15);color:#34d399">'
                f"✓ Live on {', '.join(platforms)}</span>",
                content,
                count=1,
            )
            html_path.write_text(content, encoding="utf-8")


social_content_generator = SocialContentGenerator()
