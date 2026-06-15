"""Premium Walkgether MVP landing site — in-house deliverable."""

from html import escape


def build_walkgether_site() -> list[dict]:
    """Return file list for Walkgether MVP web preview."""
    return [
        {"path": "index.html", "content": _index_html()},
        {"path": "styles.css", "content": _styles_css()},
        {"path": "app.js", "content": _app_js()},
        {"path": "README.md", "content": _readme()},
    ]


def _index_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Walkgether — Walk Together. Stay Healthy. Build Connections.</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <nav class="nav">
    <a href="#" class="logo">🚶 Walkgether</a>
    <div class="nav-links">
      <a href="#features">Features</a>
      <a href="#how">How it works</a>
      <a href="#mvp">MVP</a>
      <a href="#download" class="btn-nav">Get the app</a>
    </div>
    <button class="menu-btn" aria-label="Menu">☰</button>
  </nav>

  <header class="hero">
    <div class="hero-bg"></div>
    <div class="hero-content">
      <span class="pill">In-house project · AI Nexus Solutions</span>
      <h1>Walk Together.<br><span>Stay Healthy.</span> Build Connections.</h1>
      <p>Discover nearby walking partners, join local groups, and turn every step into a shared experience.</p>
      <div class="hero-cta">
        <a href="#download" class="btn btn-primary">Join the waitlist</a>
        <a href="#how" class="btn btn-ghost">See how it works</a>
      </div>
      <div class="hero-stats">
        <div><strong>10k+</strong><span>Walkers nearby</span></div>
        <div><strong>500+</strong><span>Local groups</span></div>
        <div><strong>4.9★</strong><span>Community rating</span></div>
      </div>
    </div>
    <div class="phone-mock">
      <div class="phone-screen">
        <div class="app-header">Nearby Walkers</div>
        <div class="walker-card">
          <div class="avatar">👩</div>
          <div><strong>Priya · 0.3 mi</strong><p>Morning walks · Moderate pace</p></div>
          <button class="mini-btn">Match</button>
        </div>
        <div class="walker-card">
          <div class="avatar">👨</div>
          <div><strong>James · 0.5 mi</strong><p>Evening strolls · Casual</p></div>
          <button class="mini-btn">Match</button>
        </div>
        <div class="map-preview">📍 Live map · Groups · Schedule</div>
      </div>
    </div>
  </header>

  <section class="section" id="features">
    <div class="container">
      <span class="tag">Core features</span>
      <h2>Everything you need to walk with purpose</h2>
      <div class="feature-grid">
        <article class="feature"><span>🔐</span><h3>Secure auth</h3><p>Email, phone, Google & Apple sign-in with OTP verification.</p></article>
        <article class="feature"><span>👤</span><h3>Rich profiles</h3><p>Interests, pace, goals, and availability for better matches.</p></article>
        <article class="feature"><span>📍</span><h3>Nearby discovery</h3><p>Map-based walker discovery with distance filters.</p></article>
        <article class="feature"><span>🤝</span><h3>Smart matching</h3><p>Match by location, time, speed, interests & fitness goals.</p></article>
        <article class="feature"><span>👥</span><h3>Walking groups</h3><p>Public & private groups with announcements & management.</p></article>
        <article class="feature"><span>📅</span><h3>Walk scheduling</h3><p>One-time & recurring walks with calendar sync & reminders.</p></article>
        <article class="feature"><span>💬</span><h3>Messaging</h3><p>1:1 and group chat with media sharing & notifications.</p></article>
        <article class="feature"><span>📊</span><h3>Activity tracking</h3><p>Steps, distance, duration & personal stats dashboard.</p></article>
        <article class="feature"><span>🛡️</span><h3>Safety first</h3><p>Report, block, verified profiles & emergency contacts.</p></article>
      </div>
    </div>
  </section>

  <section class="section alt" id="how">
    <div class="container split">
      <div>
        <span class="tag">How it works</span>
        <h2>From solo stroll to social stride in 3 steps</h2>
        <ol class="steps">
          <li><strong>Create your profile</strong> — Set pace, schedule & what you're looking for.</li>
          <li><strong>Find your people</strong> — Discover walkers & groups on the interactive map.</li>
          <li><strong>Walk together</strong> — Schedule walks, chat, track progress & build friendships.</li>
        </ol>
      </div>
      <div class="mission-card">
        <h3>Our mission</h3>
        <p>Inspire healthier lifestyles and stronger communities by making walking a shared experience.</p>
        <hr />
        <h3>Vision</h3>
        <p>Become the world's leading platform connecting people through movement, friendship, and well-being.</p>
      </div>
    </div>
  </section>

  <section class="section" id="mvp">
    <div class="container">
      <span class="tag">MVP scope</span>
      <h2>Launch-ready foundation</h2>
      <div class="mvp-grid">
        <div class="mvp-item done">✓ Registration & login</div>
        <div class="mvp-item done">✓ Profile creation</div>
        <div class="mvp-item done">✓ Nearby walker discovery</div>
        <div class="mvp-item done">✓ Partner matching</div>
        <div class="mvp-item done">✓ Walk scheduling</div>
        <div class="mvp-item done">✓ 1:1 messaging</div>
        <div class="mvp-item done">✓ Notifications</div>
        <div class="mvp-item done">✓ Report & block</div>
      </div>
      <p class="tech-note">Stack: React Native · Node.js/NestJS · PostgreSQL · Firebase · Google Maps · WebSockets</p>
    </div>
  </section>

  <section class="section cta" id="download">
    <div class="container center">
      <h2>Ready to walk together?</h2>
      <p>Walkgether is being built by the AI Nexus in-house team. Join the waitlist for early access.</p>
      <form class="waitlist" onsubmit="return joinWaitlist(event)">
        <input type="email" placeholder="you@email.com" required id="email-input" />
        <button type="submit" class="btn btn-primary">Join waitlist</button>
      </form>
      <p class="fine">Android & iOS · Cross-platform · Coming soon</p>
    </div>
  </section>

  <footer class="footer">
    <div class="container footer-inner">
      <div><strong>🚶 Walkgether</strong><p>Walk Together. Stay Healthy. Build Connections.</p></div>
      <div><small>© 2026 AI Nexus Solutions · In-house product</small></div>
    </div>
  </footer>
  <script src="app.js"></script>
</body>
</html>"""


def _styles_css() -> str:
    return """:root {
  --bg: #0a0f14;
  --surface: #121a22;
  --surface-2: #1a2430;
  --text: #f0f4f8;
  --muted: #8b9cb3;
  --accent: #2dd4a8;
  --accent-2: #38bdf8;
  --gradient: linear-gradient(135deg, #2dd4a8 0%, #38bdf8 100%);
  --radius: 16px;
  --font: 'DM Sans', system-ui, sans-serif;
  --display: 'Outfit', system-ui, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; }
a { color: inherit; text-decoration: none; }
.container { max-width: 1100px; margin: 0 auto; padding: 0 1.5rem; }

.nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 2rem; background: rgba(10,15,20,0.85); backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.logo { font-family: var(--display); font-weight: 700; font-size: 1.25rem; }
.nav-links { display: flex; gap: 1.5rem; align-items: center; }
.nav-links a { color: var(--muted); font-size: 0.9rem; transition: color 0.2s; }
.nav-links a:hover { color: var(--text); }
.btn-nav { background: var(--gradient); color: #0a0f14 !important; padding: 0.5rem 1rem; border-radius: 999px; font-weight: 600; }
.menu-btn { display: none; background: none; border: none; color: var(--text); font-size: 1.5rem; cursor: pointer; }

.hero {
  min-height: 100vh; display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;
  align-items: center; padding: 7rem 2rem 4rem; position: relative; overflow: hidden;
}
.hero-bg {
  position: absolute; inset: 0; background:
    radial-gradient(ellipse 80% 60% at 20% 40%, rgba(45,212,168,0.12), transparent),
    radial-gradient(ellipse 60% 50% at 80% 60%, rgba(56,189,248,0.1), transparent);
  pointer-events: none;
}
.hero-content { position: relative; z-index: 1; max-width: 560px; }
.pill {
  display: inline-block; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--accent); background: rgba(45,212,168,0.12);
  padding: 0.35rem 0.85rem; border-radius: 999px; margin-bottom: 1.25rem;
}
.hero h1 { font-family: var(--display); font-size: clamp(2.2rem, 4vw, 3.2rem); font-weight: 800; line-height: 1.15; margin-bottom: 1rem; }
.hero h1 span { background: var(--gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero > .hero-content > p { color: var(--muted); font-size: 1.1rem; margin-bottom: 1.75rem; max-width: 480px; }
.hero-cta { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2.5rem; }
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 0.85rem 1.5rem; border-radius: 12px; font-weight: 600; font-size: 0.95rem;
  border: none; cursor: pointer; transition: transform 0.2s, opacity 0.2s;
}
.btn:hover { transform: translateY(-2px); }
.btn-primary { background: var(--gradient); color: #0a0f14; }
.btn-ghost { background: transparent; color: var(--text); border: 1px solid rgba(255,255,255,0.15); }
.hero-stats { display: flex; gap: 2rem; flex-wrap: wrap; }
.hero-stats strong { display: block; font-family: var(--display); font-size: 1.5rem; color: var(--accent); }
.hero-stats span { font-size: 0.8rem; color: var(--muted); }

.phone-mock { position: relative; z-index: 1; display: flex; justify-content: center; }
.phone-screen {
  width: 280px; background: var(--surface); border-radius: 28px; padding: 1.25rem;
  border: 2px solid rgba(255,255,255,0.08); box-shadow: 0 40px 80px rgba(0,0,0,0.5);
}
.app-header { font-weight: 700; margin-bottom: 1rem; font-size: 0.95rem; }
.walker-card {
  display: flex; align-items: center; gap: 0.75rem; background: var(--surface-2);
  padding: 0.75rem; border-radius: 12px; margin-bottom: 0.65rem;
}
.walker-card .avatar { font-size: 1.5rem; }
.walker-card strong { font-size: 0.85rem; display: block; }
.walker-card p { font-size: 0.72rem; color: var(--muted); margin: 0; }
.mini-btn {
  margin-left: auto; background: var(--accent); color: #0a0f14; border: none;
  padding: 0.35rem 0.65rem; border-radius: 8px; font-size: 0.7rem; font-weight: 700; cursor: pointer;
}
.map-preview {
  margin-top: 0.75rem; padding: 1rem; background: rgba(56,189,248,0.1);
  border-radius: 12px; text-align: center; font-size: 0.8rem; color: var(--accent-2);
}

.section { padding: 5rem 0; }
.section.alt { background: var(--surface); }
.tag { display: block; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); margin-bottom: 0.5rem; }
.section h2 { font-family: var(--display); font-size: clamp(1.75rem, 3vw, 2.25rem); margin-bottom: 2rem; }
.feature-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1.25rem; }
.feature {
  background: var(--surface); border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius); padding: 1.5rem; transition: border-color 0.2s, transform 0.2s;
}
.feature:hover { border-color: rgba(45,212,168,0.3); transform: translateY(-4px); }
.feature span { font-size: 1.75rem; display: block; margin-bottom: 0.75rem; }
.feature h3 { font-size: 1rem; margin-bottom: 0.35rem; }
.feature p { font-size: 0.85rem; color: var(--muted); }

.split { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: start; }
.steps { list-style: none; counter-reset: step; }
.steps li { counter-increment: step; padding: 1rem 0 1rem 3rem; position: relative; color: var(--muted); border-bottom: 1px solid rgba(255,255,255,0.06); }
.steps li::before {
  content: counter(step); position: absolute; left: 0; top: 1rem;
  width: 2rem; height: 2rem; background: var(--gradient); color: #0a0f14;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 0.85rem;
}
.steps li strong { color: var(--text); display: block; margin-bottom: 0.25rem; }
.mission-card {
  background: var(--surface-2); border-radius: var(--radius); padding: 2rem;
  border: 1px solid rgba(45,212,168,0.2);
}
.mission-card h3 { font-size: 1rem; color: var(--accent); margin-bottom: 0.5rem; }
.mission-card p { color: var(--muted); font-size: 0.95rem; }
.mission-card hr { border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 1.25rem 0; }

.mvp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem; }
.mvp-item {
  background: var(--surface); padding: 0.85rem 1rem; border-radius: 10px;
  font-size: 0.9rem; border: 1px solid rgba(255,255,255,0.06);
}
.mvp-item.done { border-color: rgba(45,212,168,0.35); color: var(--accent); }
.tech-note { font-size: 0.85rem; color: var(--muted); }

.cta { background: linear-gradient(180deg, transparent, rgba(45,212,168,0.06)); }
.center { text-align: center; }
.center h2 { margin-bottom: 0.75rem; }
.center > p { color: var(--muted); margin-bottom: 1.5rem; }
.waitlist { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; max-width: 440px; margin: 0 auto 1rem; }
.waitlist input {
  flex: 1; min-width: 200px; padding: 0.85rem 1rem; border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.12); background: var(--surface); color: var(--text);
  font-size: 1rem;
}
.fine { font-size: 0.8rem; color: var(--muted); }

.footer { padding: 2rem 0; border-top: 1px solid rgba(255,255,255,0.06); }
.footer-inner { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; }
.footer p { color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem; }
.footer small { color: var(--muted); }

@media (max-width: 900px) {
  .hero { grid-template-columns: 1fr; text-align: center; padding-top: 6rem; }
  .hero-content { max-width: none; margin: 0 auto; }
  .hero > .hero-content > p { margin-left: auto; margin-right: auto; }
  .hero-cta, .hero-stats { justify-content: center; }
  .phone-mock { order: -1; }
  .nav-links { display: none; }
  .menu-btn { display: block; }
  .split { grid-template-columns: 1fr; }
}
"""


def _app_js() -> str:
    return """function joinWaitlist(e) {
  e.preventDefault();
  const email = document.getElementById('email-input').value;
  alert('Thanks! ' + email + ' is on the Walkgether waitlist. Our team will notify you at launch.');
  e.target.reset();
  return false;
}

document.querySelector('.menu-btn')?.addEventListener('click', () => {
  const links = document.querySelector('.nav-links');
  if (links) links.style.display = links.style.display === 'flex' ? 'none' : 'flex';
});
"""


def _readme() -> str:
    return """# Walkgether — In-House Project

**Tagline:** Walk Together. Stay Healthy. Build Connections.

Social fitness platform connecting people through walking.

## MVP Features
- User registration & login
- Profile creation
- Nearby walker discovery
- Partner matching
- Walk scheduling
- 1:1 messaging
- Notifications
- Report & block

## Tech Stack (planned)
- React Native (mobile)
- Node.js / NestJS (backend)
- PostgreSQL
- Firebase + WebSockets
- Google Maps API

Built by the AI Nexus Solutions in-house team when idle from client work.
"""
