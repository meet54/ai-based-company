"""Build client websites from parsed requirements — not one generic template."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from html import escape

from src.config import settings
from src.models.schemas import Project


@dataclass
class SiteSpec:
    brand_name: str
    owner_name: str
    tagline: str
    about_text: str
    phone: str = ""
    email: str = ""
    wants_carousel: bool = False
    wants_about: bool = True
    wants_contact: bool = True
    wants_ecommerce: bool = False
    page_count: int = 1
    carousel_slides: list[dict] = field(default_factory=list)
    accent: str = "#6366f1"
    accent2: str = "#8b5cf6"


THEMES = [
    ("#6366f1", "#8b5cf6"),
    ("#0ea5e9", "#06b6d4"),
    ("#10b981", "#14b8a6"),
    ("#f59e0b", "#ef4444"),
    ("#ec4899", "#a855f7"),
    ("#3b82f6", "#22d3ee"),
]


def _theme_for(seed: str) -> tuple[str, str]:
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return THEMES[h % len(THEMES)]


def _strip_meta_lines(text: str) -> str:
    """Remove budget, timeline, phone lines from display copy."""
    lines = []
    for line in text.splitlines():
        low = line.lower().strip()
        if re.match(r"^(budget|timeline|phone|pages needed|must-have features)\s*:", low):
            continue
        if re.match(r"^---", line.strip()):
            continue
        lines.append(line)
    blob = " ".join(lines)
    blob = re.sub(r"\bBudget:\s*\$?[\d,\s\-–$]+\b", "", blob, flags=re.I)
    blob = re.sub(r"\bTimeline:\s*[^.]+", "", blob, flags=re.I)
    blob = re.sub(r"\bPhone:\s*[\d\s\-+()]+", "", blob, flags=re.I)
    return re.sub(r"\s+", " ", blob).strip()


def _wants_ecommerce(text: str) -> bool:
    return bool(
        re.search(
            r"\b(e-?commerce|online store|shopping cart|add to cart|product catalog|"
            r"sell products|woocommerce|shopify store)\b",
            text,
            re.I,
        )
    )


def parse_site_spec(project: Project) -> SiteSpec:
    raw = f"{project.title}\n{project.description}\n{project.requirements or ''}"
    clean = _strip_meta_lines(raw)
    low = clean.lower()

    brand = project.client_company or project.title.split("—")[0].strip() or project.client_name
    if "—" in project.title:
        brand = project.title.split("—")[0].strip()

    owner = project.client_name or brand

    phone_m = re.search(r"Phone:\s*([+\d\s\-()]+)", project.description or "", re.I)
    phone = phone_m.group(1).strip() if phone_m else ""

    email = project.client_email or ""

    wants_carousel = bool(
        re.search(r"\b(carousel|carousol|slider|slide show|image slider)\b", low)
    )
    wants_about = bool(re.search(r"\b(about us|about section|about page|who we are)\b", low)) or True
    wants_contact = bool(
        re.search(r"\b(contact form|contact us|get in touch|reach us|inquiry)\b", low)
    ) or True
    wants_ecommerce = _wants_ecommerce(raw)

    page_m = re.search(r"(\d+)\s*page", low)
    page_count = int(page_m.group(1)) if page_m else 1

    tagline = clean[:160] if clean else f"Welcome to {brand}"
    if len(tagline) > 120 or "budget" in tagline.lower():
        tagline = f"Professional web presence for {brand}"

    about_text = (
        f"{brand} is dedicated to delivering quality service and a great experience for every visitor. "
        f"We built this site to showcase who we are and make it easy for you to get in touch."
    )
    if wants_about:
        about_m = re.search(
            r"(?:about us|about)[:\s]*(.{20,300}?)(?:contact|footer|carousel|$)",
            clean,
            re.I | re.S,
        )
        if about_m:
            about_text = about_m.group(1).strip()

    slides = []
    if wants_carousel:
        slides = [
            {"title": f"Welcome to {brand}", "caption": tagline[:80]},
            {"title": "Quality You Can Trust", "caption": "Built to your exact specifications"},
            {"title": "Let's Connect", "caption": "Reach out anytime — we're here to help"},
        ]

    accent, accent2 = _theme_for(brand + owner)

    return SiteSpec(
        brand_name=brand,
        owner_name=owner,
        tagline=tagline,
        about_text=about_text,
        phone=phone,
        email=email,
        wants_carousel=wants_carousel,
        wants_about=wants_about,
        wants_contact=wants_contact,
        wants_ecommerce=wants_ecommerce,
        page_count=page_count,
        carousel_slides=slides,
        accent=accent,
        accent2=accent2,
    )


def build_requirement_site(project: Project) -> list[dict]:
    spec = parse_site_spec(project)
    b = escape(spec.brand_name)
    owner = escape(spec.owner_name)
    tagline = escape(spec.tagline)
    about = escape(spec.about_text)
    phone = escape(spec.phone)
    email = escape(spec.email)
    a1, a2 = spec.accent, spec.accent2

    carousel_html = ""
    if spec.wants_carousel and spec.carousel_slides:
        slides_html = ""
        dots_html = ""
        for i, slide in enumerate(spec.carousel_slides):
            active = " active" if i == 0 else ""
            slides_html += f"""
        <div class="carousel-slide{active}" data-index="{i}">
          <div class="slide-bg slide-bg-{i % 3}"></div>
          <div class="slide-content">
            <h2>{escape(slide['title'])}</h2>
            <p>{escape(slide['caption'])}</p>
          </div>
        </div>"""
            dots_html += f'<button type="button" class="carousel-dot{" active" if i == 0 else ""}" data-go="{i}" aria-label="Slide {i+1}"></button>'

        carousel_html = f"""
  <section class="carousel-section" id="home" aria-label="Homepage carousel">
    <div class="carousel" id="main-carousel">
      <div class="carousel-track">{slides_html}
      </div>
      <button type="button" class="carousel-btn prev" id="carousel-prev" aria-label="Previous">‹</button>
      <button type="button" class="carousel-btn next" id="carousel-next" aria-label="Next">›</button>
      <div class="carousel-dots">{dots_html}</div>
    </div>
  </section>"""
    else:
        carousel_html = f"""
  <header id="home" class="hero-simple">
    <div class="container">
      <span class="hero-badge">Built for {owner}</span>
      <h1>{b}</h1>
      <p>{tagline}</p>
    </div>
  </header>"""

    products_html = ""
    if spec.wants_ecommerce:
        products_html = """
  <section class="section products" id="products">
    <div class="container">
      <span class="section-tag">Shop</span>
      <h2>Our Products</h2>
      <div class="product-grid">
        <article class="product-card"><div class="product-img">📦</div><h3>Product One</h3><p class="price">$29</p></article>
        <article class="product-card"><div class="product-img">📦</div><h3>Product Two</h3><p class="price">$49</p></article>
        <article class="product-card"><div class="product-img">📦</div><h3>Product Three</h3><p class="price">$39</p></article>
      </div>
    </div>
  </section>"""

    about_html = ""
    if spec.wants_about:
        about_html = f"""
  <section class="section about" id="about">
    <div class="container about-grid">
      <div>
        <span class="section-tag">About Us</span>
        <h2>About {b}</h2>
        <p>{about}</p>
        <ul class="check-list">
          <li>✓ Built to your requirements</li>
          <li>✓ Mobile-friendly design</li>
          <li>✓ Fast and easy to navigate</li>
        </ul>
      </div>
      <div class="about-visual">
        <div class="about-card">🏢 {b}</div>
        <div class="about-card accent">👤 {owner}</div>
      </div>
    </div>
  </section>"""

    contact_html = ""
    if spec.wants_contact:
        contact_extra = ""
        if phone:
            contact_extra += f'<p class="contact-detail">📞 {phone}</p>'
        if email:
            contact_extra += f'<p class="contact-detail">✉️ {email}</p>'
        contact_html = f"""
  <section class="section contact" id="contact">
    <div class="container contact-box">
      <span class="section-tag">Contact Us</span>
      <h2>Get In Touch</h2>
      <p class="section-desc">Send us a message — we will respond as soon as possible.</p>
      {contact_extra}
      <form id="contact-form" class="contact-form">
        <input type="text" name="name" placeholder="Your Name" required />
        <input type="email" name="email" placeholder="Your Email" required />
        <textarea name="message" rows="4" placeholder="Your message..." required></textarea>
        <button type="submit" class="btn btn-primary full">Contact Us</button>
      </form>
    </div>
  </section>"""

    nav_home = "#home" if spec.wants_carousel else "#home"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="{tagline}" />
  <title>{b}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <nav class="navbar">
    <div class="container nav-inner">
      <a href="{nav_home}" class="brand">{b}</a>
      <ul class="nav-links">
        <li><a href="{nav_home}">Home</a></li>
        {"<li><a href='#about'>About</a></li>" if spec.wants_about else ""}
        {"<li><a href='#contact' class='nav-cta'>Contact</a></li>" if spec.wants_contact else ""}
      </ul>
      <button class="menu-btn" aria-label="Menu">☰</button>
    </div>
  </nav>
{carousel_html}
{products_html}
{about_html}
{contact_html}

  <footer class="footer">
    <div class="container footer-inner">
      <p class="footer-name">{owner}</p>
      <p>&copy; 2026 {b}. All rights reserved.</p>
    </div>
  </footer>
  <script src="app.js"></script>
</body>
</html>"""

    css = f"""*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0b0f1a;--surface:#12182b;--surface2:#1a2238;--text:#f0f4ff;--muted:#94a3b8;--primary:{a1};--primary2:{a2};--accent:#22d3ee;--radius:16px}}
html{{scroll-behavior:smooth}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
.container{{max-width:1140px;margin:0 auto;padding:0 1.5rem}}
.navbar{{position:fixed;top:0;left:0;right:0;z-index:200;background:rgba(11,15,26,.92);backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,.06)}}
.nav-inner{{display:flex;align-items:center;justify-content:space-between;height:70px}}
.brand{{font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.25rem;color:var(--text);text-decoration:none}}
.nav-links{{display:flex;gap:2rem;list-style:none}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:.9rem;font-weight:500}}
.nav-links a:hover,.nav-cta{{color:var(--text)!important}}
.menu-btn{{display:none;background:none;border:none;color:var(--text);font-size:1.5rem;cursor:pointer}}

.carousel-section{{padding-top:70px}}
.carousel{{position:relative;max-width:100%;margin:0 auto;overflow:hidden;background:var(--surface)}}
.carousel-track{{position:relative;height:min(72vh,520px);min-height:360px}}
.carousel-slide{{position:absolute;inset:0;opacity:0;transition:opacity .6s ease;pointer-events:none}}
.carousel-slide.active{{opacity:1;pointer-events:auto}}
.slide-bg{{position:absolute;inset:0}}
.slide-bg-0{{background:linear-gradient(135deg,rgba(99,102,241,.45),rgba(15,23,42,.9)),url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 600"><rect fill="%2312182b" width="1200" height="600"/></svg>') center/cover}}
.slide-bg-1{{background:linear-gradient(135deg,rgba(14,165,233,.4),rgba(15,23,42,.9))}}
.slide-bg-2{{background:linear-gradient(135deg,rgba(16,185,129,.35),rgba(15,23,42,.9))}}
.slide-content{{position:relative;z-index:2;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:2rem}}
.slide-content h2{{font-family:'Plus Jakarta Sans',sans-serif;font-size:clamp(2rem,5vw,3.2rem);margin-bottom:1rem}}
.slide-content p{{font-size:1.1rem;color:var(--muted);max-width:520px}}
.carousel-btn{{position:absolute;top:50%;transform:translateY(-50%);z-index:10;width:48px;height:48px;border-radius:50%;border:1px solid rgba(255,255,255,.2);background:rgba(0,0,0,.4);color:white;font-size:1.75rem;cursor:pointer}}
.carousel-btn.prev{{left:1rem}}
.carousel-btn.next{{right:1rem}}
.carousel-dots{{position:absolute;bottom:1.25rem;left:50%;transform:translateX(-50%);display:flex;gap:.5rem;z-index:10}}
.carousel-dot{{width:10px;height:10px;border-radius:50%;border:none;background:rgba(255,255,255,.35);cursor:pointer}}
.carousel-dot.active{{background:var(--primary);transform:scale(1.2)}}

.hero-simple{{padding:8rem 0 4rem;text-align:center}}
.hero-simple h1{{font-family:'Plus Jakarta Sans',sans-serif;font-size:clamp(2.5rem,6vw,3.5rem);margin:.75rem 0}}
.hero-badge{{display:inline-block;padding:.35rem 1rem;background:rgba(99,102,241,.15);border-radius:50px;font-size:.8rem;color:var(--accent)}}

.section{{padding:5rem 0}}
.section-tag{{display:inline-block;font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);margin-bottom:.75rem}}
.section h2{{font-family:'Plus Jakarta Sans',sans-serif;font-size:2rem;margin-bottom:.75rem}}
.section-desc{{color:var(--muted);margin-bottom:1.5rem}}
.about-grid{{display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center}}
.check-list{{list-style:none;margin-top:1.5rem;color:var(--muted)}}
.check-list li{{padding:.4rem 0}}
.about-visual{{display:flex;flex-direction:column;gap:1rem}}
.about-card{{background:var(--surface);padding:2rem;border-radius:var(--radius);font-size:1.15rem;font-weight:600;border:1px solid rgba(255,255,255,.06)}}
.about-card.accent{{background:linear-gradient(135deg,rgba(99,102,241,.2),rgba(34,211,238,.08));border-color:rgba(99,102,241,.3)}}
.contact-box{{max-width:560px;margin:0 auto;text-align:center}}
.contact-detail{{color:var(--muted);margin:.35rem 0}}
.contact-form{{display:flex;flex-direction:column;gap:1rem;margin-top:1.5rem;text-align:left}}
.contact-form input,.contact-form textarea{{padding:1rem;background:var(--surface);border:1px solid rgba(255,255,255,.1);border-radius:12px;color:var(--text);font-family:inherit}}
.btn{{display:inline-flex;align-items:center;justify-content:center;padding:.85rem 1.75rem;border-radius:12px;font-weight:600;border:none;cursor:pointer}}
.btn-primary{{background:linear-gradient(135deg,var(--primary),var(--primary2));color:white}}
.btn.full{{width:100%}}
.product-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.5rem;margin-top:2rem}}
.product-card{{background:var(--surface2);border-radius:var(--radius);padding:1.5rem;text-align:center}}
.product-img{{font-size:2.5rem;margin-bottom:.75rem}}
.price{{color:var(--accent);font-weight:700}}
.footer{{padding:2.5rem 0;border-top:1px solid rgba(255,255,255,.06);text-align:center}}
.footer-name{{font-size:1.15rem;font-weight:700;color:var(--text);margin-bottom:.35rem}}
.footer p{{color:var(--muted);font-size:.9rem}}
@media(max-width:768px){{.nav-links{{display:none}}.menu-btn{{display:block}}.about-grid{{grid-template-columns:1fr}}.carousel-track{{min-height:300px}}}}"""

    js = """(function () {
  const track = document.querySelector('.carousel-track');
  if (track) {
    const slides = [...track.querySelectorAll('.carousel-slide')];
    const dots = [...document.querySelectorAll('.carousel-dot')];
    let idx = 0;
    let timer;

    function show(i) {
      idx = (i + slides.length) % slides.length;
      slides.forEach((s, n) => s.classList.toggle('active', n === idx));
      dots.forEach((d, n) => d.classList.toggle('active', n === idx));
    }

    function next() { show(idx + 1); }
    function prev() { show(idx - 1); }

    document.getElementById('carousel-next')?.addEventListener('click', () => { next(); reset(); });
    document.getElementById('carousel-prev')?.addEventListener('click', () => { prev(); reset(); });
    dots.forEach(d => d.addEventListener('click', () => { show(Number(d.dataset.go)); reset(); }));

    function reset() {
      clearInterval(timer);
      timer = setInterval(next, 5000);
    }
    if (slides.length) reset();
  }

  document.querySelector('.menu-btn')?.addEventListener('click', () => {
    const links = document.querySelector('.nav-links');
    if (links) links.style.display = links.style.display === 'flex' ? 'none' : 'flex';
  });

  document.getElementById('contact-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const orig = btn.textContent;
    btn.textContent = '✓ Sent!';
    btn.style.background = '#22c55e';
    setTimeout(() => { btn.textContent = orig; btn.style.background = ''; e.target.reset(); }, 2500);
  });

  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (id && id.length > 1) {
        e.preventDefault();
        document.querySelector(id)?.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
})();"""

    readme = f"""# {spec.brand_name}

Site built for **{spec.owner_name}** per client requirements.

## Sections included
- Carousel: {'Yes' if spec.wants_carousel else 'No'}
- About Us: {'Yes' if spec.wants_about else 'No'}
- Contact form: {'Yes' if spec.wants_contact else 'No'}
- Product shop: {'Yes' if spec.wants_ecommerce else 'No (not requested)'}

## Run
Open `index.html` in a browser.

Generated by {settings.company_name}.
"""

    return [
        {"path": "index.html", "content": html},
        {"path": "styles.css", "content": css},
        {"path": "app.js", "content": js},
        {"path": "README.md", "content": readme},
    ]
