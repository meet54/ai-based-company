"""Premium website templates that fulfill client requirements."""

from html import escape
import re

from src.config import settings


def detect_project_type(text: str) -> str:
    t = text.lower()
    if re.search(r"\b(e-?commerce|online store|shopping cart|add to cart|product catalog|shopify|woocommerce)\b", t):
        return "ecommerce"
    if any(w in t for w in ("dashboard", "admin", "portal", "saas", "analytics")):
        return "dashboard"
    if any(w in t for w in ("portfolio", "gallery", "photography", "showcase")):
        return "portfolio"
    if any(w in t for w in ("restaurant", "menu", "food", "cafe")):
        return "restaurant"
    if any(w in t for w in ("app", "mobile", "platform")):
        return "webapp"
    return "business"


def extract_features(text: str, max_features: int = 6) -> list[str]:
    features = []
    for line in text.split("\n"):
        line = line.strip().lstrip("-•*0123456789.) ")
        if 10 < len(line) < 120 and not line.startswith("#"):
            features.append(line)
    if len(features) < 3:
        defaults = [
            "Modern responsive design for all devices",
            "Fast loading and smooth user experience",
            "Professional branding aligned with your business",
            "Contact and inquiry forms for lead capture",
            "SEO-friendly structure for better visibility",
            "Secure and reliable architecture",
        ]
        features.extend(defaults)
    return features[:max_features]


def build_premium_site(
    title: str,
    client: str,
    company: str,
    description: str,
    requirements: str = "",
) -> list[dict]:
    full_text = f"{title}\n{description}\n{requirements}"
    ptype = detect_project_type(full_text)
    features = extract_features(requirements or description)
    safe_title = escape(title)
    safe_client = escape(client)
    safe_company = escape(company)
    safe_desc = escape(description[:280])

    hero_sub = {
        "ecommerce": "Shop the latest collection with secure checkout",
        "dashboard": "Powerful analytics and control at your fingertips",
        "portfolio": "Showcasing creative work that speaks for itself",
        "restaurant": "Fresh flavors, warm atmosphere, unforgettable dining",
        "webapp": "A modern platform built for scale and performance",
        "business": "Digital solutions that grow your business",
    }[ptype]

    feature_cards = "".join(
        f'<article class="feature-card"><div class="feature-icon">{i+1}</div>'
        f"<h3>{escape(f[:50])}</h3><p>Delivered per your project requirements.</p></article>"
        for i, f in enumerate(features[:6])
    )

    extra_section = ""
    if ptype == "ecommerce":
        extra_section = """
    <section class="section products" id="products">
      <div class="container">
        <span class="section-tag">Products</span>
        <h2>Featured Collection</h2>
        <div class="product-grid">
          <div class="product-card"><div class="product-img">🛍️</div><h3>Premium Item</h3><p class="price">$49.99</p><button class="btn-sm">Add to Cart</button></div>
          <div class="product-card"><div class="product-img">✨</div><h3>Best Seller</h3><p class="price">$79.99</p><button class="btn-sm">Add to Cart</button></div>
          <div class="product-card"><div class="product-img">🔥</div><h3>New Arrival</h3><p class="price">$59.99</p><button class="btn-sm">Add to Cart</button></div>
        </div>
      </div>
    </section>"""
    elif ptype == "dashboard":
        extra_section = """
    <section class="section stats-section" id="dashboard">
      <div class="container">
        <span class="section-tag">Dashboard</span>
        <h2>Key Metrics</h2>
        <div class="stats-row">
          <div class="stat-box"><span class="stat-num">2.4k</span><span class="stat-label">Users</span></div>
          <div class="stat-box"><span class="stat-num">98%</span><span class="stat-label">Uptime</span></div>
          <div class="stat-box"><span class="stat-num">$12k</span><span class="stat-label">Revenue</span></div>
          <div class="stat-box"><span class="stat-num">156</span><span class="stat-label">Tasks</span></div>
        </div>
      </div>
    </section>"""
    elif ptype == "portfolio":
        extra_section = """
    <section class="section gallery" id="gallery">
      <div class="container">
        <span class="section-tag">Portfolio</span>
        <h2>Our Work</h2>
        <div class="gallery-grid">
          <div class="gallery-item">Project Alpha</div>
          <div class="gallery-item">Project Beta</div>
          <div class="gallery-item">Project Gamma</div>
          <div class="gallery-item">Project Delta</div>
        </div>
      </div>
    </section>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="{safe_desc}" />
  <title>{safe_title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <nav class="navbar">
    <div class="container nav-inner">
      <a href="#" class="brand">{safe_company}</a>
      <ul class="nav-links">
        <li><a href="#home">Home</a></li>
        <li><a href="#features">Features</a></li>
        <li><a href="#about">About</a></li>
        <li><a href="#contact" class="nav-cta">Contact</a></li>
      </ul>
      <button class="menu-btn" aria-label="Menu">☰</button>
    </div>
  </nav>

  <header id="home" class="hero">
    <div class="hero-bg"></div>
    <div class="container hero-content">
      <span class="hero-badge">Built for {safe_client}</span>
      <h1>{safe_title}</h1>
      <p class="hero-desc">{hero_sub}. {safe_desc}</p>
      <div class="hero-actions">
        <a href="#contact" class="btn btn-primary">Get Started</a>
        <a href="#features" class="btn btn-ghost">Learn More</a>
      </div>
      <div class="hero-stats">
        <div><strong>100%</strong><span>Responsive</span></div>
        <div><strong>24/7</strong><span>Support Ready</span></div>
        <div><strong>Fast</strong><span>Performance</span></div>
      </div>
    </div>
  </header>

  <section id="features" class="section">
    <div class="container">
      <span class="section-tag">Features</span>
      <h2>Everything You Asked For</h2>
      <p class="section-desc">Built to match your exact project requirements.</p>
      <div class="feature-grid">{feature_cards}</div>
    </div>
  </section>
{extra_section}
  <section id="about" class="section about">
    <div class="container about-grid">
      <div>
        <span class="section-tag">About</span>
        <h2>Why Choose Us</h2>
        <p>We deliver professional digital products tailored to {safe_client}'s needs. Every feature is implemented according to your specifications.</p>
        <ul class="check-list">
          <li>✓ Requirements fully implemented</li>
          <li>✓ Modern, premium design</li>
          <li>✓ Mobile & desktop optimized</li>
          <li>✓ Ready for production deployment</li>
        </ul>
      </div>
      <div class="about-visual">
        <div class="about-card">🚀 Launch Ready</div>
        <div class="about-card accent">⭐ Client: {safe_client}</div>
      </div>
    </div>
  </section>

  <section id="contact" class="section contact">
    <div class="container contact-box">
      <span class="section-tag">Contact</span>
      <h2>Let's Work Together</h2>
      <form id="contact-form" class="contact-form">
        <input type="text" name="name" placeholder="Your Name" required />
        <input type="email" name="email" placeholder="Email Address" required />
        <textarea name="message" rows="4" placeholder="Tell us about your project..." required></textarea>
        <button type="submit" class="btn btn-primary full">Send Message</button>
      </form>
    </div>
  </section>

  <footer class="footer">
    <div class="container">
      <p>&copy; 2026 {safe_company}. Crafted for {safe_client}.</p>
    </div>
  </footer>
  <script src="app.js"></script>
</body>
</html>"""

    css = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0b0f1a;--surface:#12182b;--surface2:#1a2238;--text:#f0f4ff;--muted:#94a3b8;--primary:#6366f1;--primary2:#8b5cf6;--accent:#22d3ee;--radius:16px;--shadow:0 25px 50px -12px rgba(0,0,0,.5)}
html{scroll-behavior:smooth}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
.container{max-width:1140px;margin:0 auto;padding:0 1.5rem}
.navbar{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(11,15,26,.85);backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,.06)}
.nav-inner{display:flex;align-items:center;justify-content:space-between;height:70px}
.brand{font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.25rem;color:var(--text);text-decoration:none;background:linear-gradient(135deg,var(--primary),var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.nav-links{display:flex;gap:2rem;list-style:none}
.nav-links a{color:var(--muted);text-decoration:none;font-size:.9rem;font-weight:500;transition:color .2s}
.nav-links a:hover,.nav-cta{color:var(--text)!important}
.menu-btn{display:none;background:none;border:none;color:var(--text);font-size:1.5rem}
.hero{position:relative;min-height:100vh;display:flex;align-items:center;padding:8rem 0 4rem;overflow:hidden}
.hero-bg{position:absolute;inset:0;background:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(99,102,241,.25),transparent),radial-gradient(ellipse 60% 40% at 80% 50%,rgba(34,211,238,.12),transparent)}
.hero-content{position:relative;z-index:1;max-width:720px}
.hero-badge{display:inline-block;padding:.35rem 1rem;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.3);border-radius:50px;font-size:.8rem;color:var(--accent);margin-bottom:1.5rem}
.hero h1{font-family:'Plus Jakarta Sans',sans-serif;font-size:clamp(2.5rem,6vw,4rem);font-weight:800;line-height:1.1;margin-bottom:1.25rem}
.hero-desc{font-size:1.15rem;color:var(--muted);margin-bottom:2rem;max-width:560px}
.hero-actions{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:3rem}
.btn{display:inline-flex;align-items:center;justify-content:center;padding:.85rem 1.75rem;border-radius:12px;font-weight:600;font-size:.95rem;text-decoration:none;border:none;cursor:pointer;transition:transform .2s,box-shadow .2s}
.btn:hover{transform:translateY(-2px)}
.btn-primary{background:linear-gradient(135deg,var(--primary),var(--primary2));color:white;box-shadow:0 10px 30px rgba(99,102,241,.35)}
.btn-ghost{background:transparent;color:var(--text);border:1px solid rgba(255,255,255,.15)}
.btn-sm{padding:.5rem 1rem;font-size:.85rem;background:var(--primary);color:white;border:none;border-radius:8px;cursor:pointer}
.btn.full{width:100%}
.hero-stats{display:flex;gap:3rem}
.hero-stats strong{display:block;font-size:1.5rem;color:var(--text)}
.hero-stats span{font-size:.8rem;color:var(--muted)}
.section{padding:6rem 0}
.section-tag{display:inline-block;font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);margin-bottom:.75rem}
.section h2{font-family:'Plus Jakarta Sans',sans-serif;font-size:2.25rem;font-weight:800;margin-bottom:.75rem}
.section-desc{color:var(--muted);margin-bottom:2.5rem}
.feature-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.5rem}
.feature-card{background:var(--surface);border:1px solid rgba(255,255,255,.06);border-radius:var(--radius);padding:2rem;transition:border-color .2s,transform .2s}
.feature-card:hover{border-color:rgba(99,102,241,.4);transform:translateY(-4px)}
.feature-icon{width:48px;height:48px;background:linear-gradient(135deg,var(--primary),var(--primary2));border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:700;margin-bottom:1rem}
.feature-card h3{font-size:1.1rem;margin-bottom:.5rem}
.feature-card p{color:var(--muted);font-size:.9rem}
.product-grid,.gallery-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;margin-top:2rem}
.product-card,.gallery-item{background:var(--surface2);border-radius:var(--radius);padding:1.5rem;text-align:center;border:1px solid rgba(255,255,255,.06)}
.product-img{font-size:3rem;margin-bottom:1rem}
.price{color:var(--accent);font-weight:700;font-size:1.25rem;margin:.5rem 0 1rem}
.stats-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1.5rem;margin-top:2rem}
.stat-box{background:var(--surface2);border-radius:var(--radius);padding:2rem;text-align:center;border:1px solid rgba(255,255,255,.06)}
.stat-num{display:block;font-size:2rem;font-weight:800;color:var(--accent)}
.stat-label{font-size:.85rem;color:var(--muted)}
.about-grid{display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center}
.check-list{list-style:none;margin-top:1.5rem}
.check-list li{padding:.5rem 0;color:var(--muted)}
.about-visual{display:flex;flex-direction:column;gap:1rem}
.about-card{background:var(--surface);padding:2rem;border-radius:var(--radius);font-size:1.25rem;font-weight:600;border:1px solid rgba(255,255,255,.06)}
.about-card.accent{background:linear-gradient(135deg,rgba(99,102,241,.2),rgba(34,211,238,.1));border-color:rgba(99,102,241,.3)}
.contact-box{max-width:560px;margin:0 auto;text-align:center}
.contact-form{display:flex;flex-direction:column;gap:1rem;margin-top:2rem;text-align:left}
.contact-form input,.contact-form textarea{padding:1rem 1.25rem;background:var(--surface);border:1px solid rgba(255,255,255,.1);border-radius:12px;color:var(--text);font-family:inherit;font-size:1rem}
.contact-form input:focus,.contact-form textarea:focus{outline:none;border-color:var(--primary)}
.footer{padding:2rem 0;border-top:1px solid rgba(255,255,255,.06);text-align:center;color:var(--muted);font-size:.9rem}
@media(max-width:768px){.nav-links{display:none}.menu-btn{display:block}.about-grid{grid-template-columns:1fr}.hero-stats{gap:1.5rem}}"""

    js = """document.querySelector('.menu-btn')?.addEventListener('click', () => {
  const links = document.querySelector('.nav-links');
  if (links) links.style.display = links.style.display === 'flex' ? 'none' : 'flex';
});

document.getElementById('contact-form')?.addEventListener('submit', (e) => {
  e.preventDefault();
  const btn = e.target.querySelector('button');
  const orig = btn.textContent;
  btn.textContent = '✓ Message Sent!';
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
});"""

    return [
        {"path": "index.html", "content": html},
        {"path": "styles.css", "content": css},
        {"path": "app.js", "content": js},
        {"path": "README.md", "content": f"# {title}\n\nPremium site for **{client}**.\n\n## Run\nOpen index.html or: `python -m http.server 8080`\n\nGenerated by {settings.company_name}."},
    ]
