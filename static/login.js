async function loadBranding() {
  try {
    const res = await fetch('/api/auth/info');
    if (res.ok) {
      const data = await res.json();
      document.getElementById('company-name').textContent = data.company_name || 'AI Nexus Solutions';
    }
  } catch {
    /* use default title */
  }
}

function showError(msg) {
  const el = document.getElementById('login-error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('login-btn');
  const form = e.target;
  const email = form.email.value.trim();
  const password = form.password.value;

  document.getElementById('login-error').classList.add('hidden');
  btn.disabled = true;
  btn.textContent = 'Signing in…';

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showError(data.detail || 'Invalid email or password');
      return;
    }
    window.location.href = '/';
  } catch {
    showError('Could not reach server. Is it running?');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Sign in to Dashboard';
  }
});

loadBranding();
