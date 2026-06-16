const STAGE_LABELS = {
  lead_generation: 'Lead Generation',
  requirement_gathering: 'Requirements',
  quotation: 'Quotation',
  ceo_approval: 'CEO Approval',
  project_kickoff: 'Kickoff',
  development: 'Development',
  team_leader_review: 'Team Review',
  qa_testing: 'QA Testing',
  client_handover: 'Handover',
  payment_collection: 'Payment',
  project_closed: 'Closed',
};

const STAGE_AGENTS = {
  lead_generation: 'Marketing + Sales',
  requirement_gathering: 'Sales + Business Analyst',
  quotation: 'Finance + BA',
  ceo_approval: 'YOU (CEO)',
  project_kickoff: 'PM + HR',
  development: 'Frontend + Backend + Full-Stack Devs',
  team_leader_review: 'Project Manager',
  qa_testing: 'QA Tester',
  client_handover: 'Client Success + Sales',
  payment_collection: 'Finance → Your Account',
  project_closed: 'Project Manager',
};

const WORKFLOW_DETAILS = [
  { title: 'Find Clients', desc: 'Marketing runs campaigns. Sales qualifies inbound leads and schedules discovery calls.', agents: 'Priya (Marketing), Alex (Sales)' },
  { title: 'Gather Requirements', desc: 'Sales talks with the client. Business Analyst creates formal specs and recommends tech stack.', agents: 'Alex (Sales), Sam (BA)' },
  { title: 'Generate Quotation', desc: 'Finance creates itemized quote with hours, rates, tax, and payment terms.', agents: 'Nina (Finance)' },
  { title: 'CEO Approval', desc: 'You review and approve/reject the quotation before work begins.', agents: 'YOU' },
  { title: 'Assign Team & Kickoff', desc: 'PM plans sprints. HR assigns the right developers based on skills.', agents: 'Morgan (PM), Jordan (HR)' },
  { title: 'Development', desc: 'Developers build the website/software per requirements.', agents: 'Riya, David, Elena' },
  { title: 'Team Leader Review', desc: 'PM cross-checks code quality, completeness, and requirement alignment.', agents: 'Morgan (PM)' },
  { title: 'QA Testing', desc: 'Tester runs test cases, finds bugs, and gives pass/fail verdict.', agents: 'Chris (QA)' },
  { title: 'Client Handover', desc: 'Deliver source code, docs, training. Get client sign-off.', agents: 'Taylor (Client Success)' },
  { title: 'Payment Collection', desc: 'Invoice sent. Payment deposited to your CEO business account.', agents: 'Nina (Finance)' },
];

let company = {};
let currentPreviewId = null;
let monitorInterval = null;
let leadsPollInterval = null;

const ROLE_EMOJI = {
  sales: '💼', marketing: '📣', hr: '🧑‍💼', business_analyst: '📋',
  project_manager: '📌', frontend_developer: '🎨', backend_developer: '⚙️',
  fullstack_developer: '🔧', mobile_developer: '📱', app_developer: '📲',
  qa_tester: '🔍', finance: '💰', client_success: '🤝',
};

function isProjectDone(p) {
  return p.is_done || p.status === 'completed' || p.current_stage === 'project_closed';
}

function getPreviewedProjects() {
  try {
    return JSON.parse(localStorage.getItem('previewedProjects') || '[]');
  } catch {
    return [];
  }
}

function isProjectPreviewed(projectId) {
  return getPreviewedProjects().includes(Number(projectId));
}

function markProjectPreviewed(projectId) {
  const ids = getPreviewedProjects();
  const id = Number(projectId);
  if (!ids.includes(id)) {
    ids.push(id);
    localStorage.setItem('previewedProjects', JSON.stringify(ids));
  }
  refreshNotificationUI();
}

function getUnpreviewedCompleted(projects) {
  return (projects || []).filter(p => p.preview_available && !isProjectPreviewed(p.id));
}

function refreshNotificationUI() {
  api('/dashboard').then(d => {
    renderNotifications(d.notifications);
    const activeView = document.querySelector('.view.active')?.id;
    if (activeView === 'view-dashboard') {
      const projectsEl = document.getElementById('recent-projects');
      if (projectsEl && d.recent_projects) {
        projectsEl.innerHTML = d.recent_projects.length
          ? d.recent_projects.map(p => renderProjectCard(p, { compact: true })).join('')
          : '<div class="list-empty">No projects yet.</div>';
      }
    } else if (activeView === 'view-projects') {
      loadProjects();
    }
  }).catch(() => {});
}

function renderProjectCard(p, { compact = false } = {}) {
  const done = isProjectDone(p);
  const canPreview = p.preview_available;
  const previewed = canPreview && isProjectPreviewed(p.id);
  const showDoneAlert = done && canPreview && !previewed;
  const cardClass = showDoneAlert ? 'project-card done' : 'project-card' + (done ? ' project-card-completed' : '');

  return `
    <div class="${cardClass}" onclick="openProject(${p.id})" style="${compact ? 'margin-bottom:0.75rem' : ''}">
      ${showDoneAlert ? '<span class="done-ribbon">✓ DONE</span>' : ''}
      ${previewed ? '<span class="viewed-badge">✓ Viewed</span>' : ''}
      <h4>${escapeHtml(p.title)}</h4>
      <div class="client">${escapeHtml(p.client_company)} — ${compact ? escapeHtml(p.client_name) : escapeHtml(p.client_email)}</div>
      <div class="project-card-footer">
        <span class="stage-badge ${stageBadgeClass(p.current_stage)}">${formatStage(p.current_stage)}</span>
        <div style="display:flex;align-items:center;gap:0.5rem">
          ${p.quotation_total && !canPreview ? `<span style="color:var(--success);font-weight:600">$${p.quotation_total.toLocaleString()}</span>` : ''}
          ${canPreview ? previewButton(p.id, p.title, previewed ? 'View Again' : 'Preview') : ''}
        </div>
      </div>
    </div>
  `;
}

function updateProjectsBadge(count) {
  const badge = document.getElementById('projects-badge');
  if (count > 0) {
    badge.textContent = count;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

function renderNotifications(notifications) {
  const unpreviewed = getUnpreviewedCompleted(notifications?.projects || []);
  const count = unpreviewed.length;
  updateProjectsBadge(count);

  const banner = document.getElementById('notification-banner');
  if (!count) {
    banner.classList.add('hidden');
    return;
  }

  const names = unpreviewed.slice(0, 3).map(p => p.title).join(', ');
  banner.classList.remove('hidden');
  banner.innerHTML = `
    <p>🎉 <strong>${count} project${count > 1 ? 's' : ''} ready to preview</strong>${names ? `: ${escapeHtml(names)}` : ''}</p>
    <button class="btn btn-success btn-sm" onclick="goToCompletedProjects()">View Projects</button>
  `;
}

function goToCompletedProjects() {
  document.querySelector('[data-view="projects"]').click();
}

async function api(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Please sign in');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = typeof err.detail === 'string'
      ? err.detail
      : Array.isArray(err.detail)
        ? err.detail.map(d => d.msg || d).join(', ')
        : 'Request failed';
    throw new Error(detail);
  }
  return res.json();
}

function showToast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type}`;
  setTimeout(() => el.classList.add('hidden'), 4000);
}

function formatStage(stage) {
  return STAGE_LABELS[stage] || stage;
}

function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function stageBadgeClass(stage) {
  if (stage === 'ceo_approval') return 'ceo';
  if (stage === 'project_closed') return 'done';
  return 'active';
}

// Navigation
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`view-${btn.dataset.view}`).classList.add('active');
    loadView(btn.dataset.view);
  });
});

async function loadView(view) {
  if (monitorInterval) { clearInterval(monitorInterval); monitorInterval = null; }
  if (view !== 'office') OfficeSimulator.stop();
  if (view === 'dashboard') await loadDashboard();
  if (view === 'freelancing') await loadFreelancingView();
  if (view === 'inhouse') await loadInhouseView();
  if (view === 'office') await loadLiveOffice();
  if (view === 'projects') await loadProjects();
  if (view === 'team') await loadTeamMonitor();
  if (view === 'workflow') renderWorkflow();
  if (view === 'activity') await loadActivity();
}

async function loadLiveOffice() {
  OfficeSimulator.start('virtual-office');

  const render = async () => {
    const data = await api('/team/live');
    const wg = data.inhouse_project;
    const phase = OfficeSimulator.officePhase();
    const phaseNote = phase === 'closed' ? ' · Office closed' : '';
    const statsEl = document.getElementById('office-stats');
    if (statsEl) {
      statsEl.textContent =
        `${data.working_count} working · ${data.idle_count} idle · ${data.active_projects} client projects` +
        (wg ? ` · 🚶 Walkgether ${wg.progress_percent}%` : '') + phaseNote;
    }
    await OfficeSimulator.sync(data.members);
  };

  await render();
  monitorInterval = setInterval(render, 2500);
}

async function loadTeamMonitor() {
  const monitorCardClass = (m) => {
    if (m.status === 'working') return 'working';
    if (m.office_activity === 'coffee') return 'coffee';
    if (m.office_activity === 'phone') return 'phone';
    if (m.office_activity === 'gaming') return 'gaming';
    if (m.office_activity === 'query') return 'query';
    return 'idle';
  };

  const monitorTaskPrefix = (m) => {
    if (m.status === 'working') return '🟢 ';
    if (m.office_activity === 'coffee') return '☕ ';
    if (m.office_activity === 'phone') return '📞 ';
    if (m.office_activity === 'gaming') return '🎮 ';
    if (m.office_activity === 'query') return '💬 ';
    return '⚪ ';
  };

  const monitorStatusClass = (m) => {
    if (m.status === 'working') return 'working';
    if (m.office_activity === 'coffee') return 'coffee';
    if (m.office_activity === 'phone') return 'phone';
    if (m.office_activity === 'gaming') return 'gaming';
    if (m.office_activity === 'query') return 'query';
    return m.status;
  };

  const monitorStatusLabel = (m) => {
    if (m.status === 'working') return 'Currently Working';
    if (m.office_activity === 'coffee') return 'Coffee Break';
    if (m.office_activity === 'phone') return 'On a Call';
    if (m.office_activity === 'gaming') return 'Games Room';
    if (m.office_activity === 'query') return 'Team Q&A';
    return 'Last Activity';
  };

  const render = async () => {
    const data = await api('/team/live');
    const wg = data.inhouse_project;
    const coffeeCount = data.members.filter(m => m.office_activity === 'coffee').length;
    const phoneCount = data.members.filter(m => m.office_activity === 'phone').length;
    const gameCount = data.members.filter(m => m.office_activity === 'gaming').length;
    const queryCount = data.members.filter(m => m.office_activity === 'query').length;
    const socialParts = [];
    if (coffeeCount) socialParts.push(`☕ ${coffeeCount} coffee`);
    if (phoneCount) socialParts.push(`📞 ${phoneCount} on call`);
    if (gameCount) socialParts.push(`🎮 ${gameCount} gaming`);
    if (queryCount) socialParts.push(`💬 ${queryCount} Q&A`);
    const socialNote = socialParts.length ? ` · ${socialParts.join(' · ')}` : '';

    document.getElementById('monitor-stats').textContent =
      `${data.working_count} working · ${data.idle_count} idle · ${data.active_projects} client projects` +
      (wg ? ` · 🚶 Walkgether ${wg.progress_percent}%` : '') + socialNote;

    document.getElementById('team-monitor-grid').innerHTML = data.members.map(m => `
      <div class="monitor-card ${monitorCardClass(m)} ${m.inhouse ? 'inhouse' : ''}">
        <div class="monitor-top">
          <div class="monitor-avatar">
            ${m.office_activity === 'coffee' ? '☕' : m.office_activity === 'phone' ? '📞' : m.office_activity === 'gaming' ? '🎮' : m.office_activity === 'query' ? '💬' : (ROLE_EMOJI[m.role] || '🤖')}
            <span class="status-dot ${monitorStatusClass(m)}"></span>
          </div>
          <div>
            <div class="monitor-name">${escapeHtml(m.name)}</div>
            <div class="monitor-role">${m.department}</div>
          </div>
        </div>
        <div class="monitor-task">${monitorTaskPrefix(m)}${escapeHtml(m.current_task)}</div>
        ${m.conversation_partner ? `<div class="monitor-partner">with ${escapeHtml(m.conversation_partner)}</div>` : ''}
        ${m.project_title ? `<div class="monitor-project ${m.inhouse ? 'inhouse-project' : ''}">📁 ${escapeHtml(m.project_title)}</div>` : ''}
        <div class="monitor-tooltip">
          <h5>${escapeHtml(m.name)} — ${monitorStatusLabel(m)}</h5>
          <p><strong>Role:</strong> ${m.role.replace(/_/g, ' ')}</p>
          <p><strong>Task:</strong> ${escapeHtml(m.current_task)}</p>
          ${m.conversation_partner ? `<p><strong>With:</strong> ${escapeHtml(m.conversation_partner)}</p>` : ''}
          ${m.office_query ? `<p><strong>Question:</strong> ${escapeHtml(m.office_query)}</p>` : ''}
          ${m.office_answer && m.office_activity === 'query' ? `<p><strong>Answer:</strong> ${escapeHtml(m.office_answer)}</p>` : ''}
          ${m.project_title ? `<p><strong>Project:</strong> ${escapeHtml(m.project_title)}</p>` : ''}
          ${m.stage ? `<p><strong>Stage:</strong> ${formatStage(m.stage)}</p>` : ''}
          <div class="tooltip-detail">${escapeHtml(m.work_details)}</div>
        </div>
      </div>
    `).join('');

    const logs = await api('/activity?limit=12');
    document.getElementById('monitor-feed').innerHTML = logs.length
      ? logs.map(a => `
        <div class="activity-item">
          <span class="time">${formatTime(a.created_at)}</span>
          <div><span class="agent">${escapeHtml(a.agent_name)}</span> — ${escapeHtml(a.action)}</div>
        </div>
      `).join('')
      : '<div class="list-empty">No activity yet. Start a project to see your team work!</div>';
  };

  await render();
  monitorInterval = setInterval(render, 2500);
}

async function logout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
  } finally {
    window.location.href = '/login';
  }
}

async function init() {
  company = await api('/company');
  document.getElementById('company-name').textContent = company.name;
  document.getElementById('ceo-name').textContent = company.ceo_name;
  document.getElementById('ceo-email').textContent = company.ceo_email;
  document.getElementById('ceo-greeting').textContent = company.ceo_name;
  document.getElementById('demo-badge').classList.add('hidden');
  document.getElementById('real-badge').classList.add('hidden');
  document.getElementById('key-badge').classList.add('hidden');
  if (company.ai_mode === 'real') {
    const badge = document.getElementById('real-badge');
    badge.textContent = `Real AI · ${company.provider} · ${company.model || ''}`;
    badge.classList.remove('hidden');
  } else if (company.ai_mode === 'missing_key') {
    document.getElementById('key-badge').classList.remove('hidden');
  } else {
    document.getElementById('demo-badge').classList.remove('hidden');
  }
  await loadDashboard();
  startLeadsPolling();
  refreshLiveLeads();
}

function startLeadsPolling() {
  if (leadsPollInterval) clearInterval(leadsPollInterval);
  leadsPollInterval = setInterval(refreshLiveLeads, 30000);
}

function renderLiveLeads(leadsData) {
  const status = leadsData?.status || {};
  const leads = leadsData?.items || leadsData?.leads || [];
  const statusEl = document.getElementById('leads-scan-status');
  const badgeEl = document.getElementById('leads-count-badge');
  const listEl = document.getElementById('live-leads-list');

  if (statusEl) {
    const sources = (status.last_scan_sources || []).join(', ') || 'Reddit, HN, Remote OK, Jobicy';
    const when = status.last_scan_at
      ? `Last scan: ${formatTime(status.last_scan_at)}`
      : 'Auto-scan every 90s';
    const regions = (status.target_regions || ['USA', 'UK', 'EU', 'India', 'Japan']).join(' · ');
    statusEl.textContent = status.scanning
      ? `Scanning freelance gigs in ${regions}…`
      : `${when} · Regions: ${regions} (no Germany)`;
  }
  if (badgeEl) {
    badgeEl.textContent = `${status.new_leads ?? leads.length} new`;
  }
  const navBadge = document.getElementById('freelancing-badge');
  if (navBadge) {
    const count = status.new_leads ?? leads.length;
    if (count > 0) {
      navBadge.textContent = count;
      navBadge.classList.remove('hidden');
    } else {
      navBadge.classList.add('hidden');
    }
  }
  if (!listEl) return;

  if (!leads.length) {
    listEl.innerHTML = `<div class="list-empty">${
      status.scanning
        ? 'Scanning r/forhire, r/freelance, r/jobbit & HN for paid freelance work…'
        : 'No freelance gigs found yet. Click <strong>Scan Freelance Gigs</strong> or wait for auto-scan.'
    }</div>`;
    return;
  }

  listEl.innerHTML = leads.map(lead => `
    <div class="lead-card" data-lead-id="${escapeHtml(lead.id)}">
      <div class="lead-card-main">
        <span class="lead-platform">${lead.platform_icon || '📌'} ${escapeHtml(lead.platform_label)}</span>
        <span class="lead-type-badge">${escapeHtml(lead.gig_type || 'Freelance')}</span>
        ${lead.region ? `<span class="lead-region-badge">${escapeHtml(lead.region)}</span>` : ''}
        <h4>${escapeHtml(lead.company_name)} — ${escapeHtml(lead.title)}</h4>
        <p class="lead-desc">${escapeHtml((lead.description || '').slice(0, 220))}${(lead.description || '').length > 220 ? '…' : ''}</p>
        <div class="lead-meta">
          <span class="lead-score">Match ${lead.score}%</span>
          ${lead.budget_hint ? `<span class="lead-budget">💰 ${escapeHtml(lead.budget_hint)}</span>` : ''}
          · ${escapeHtml(lead.contact_name)}
          · ${escapeHtml(lead.location || 'Remote')}
        </div>
      </div>
      <div class="lead-actions">
        <button type="button" class="btn btn-success btn-sm" onclick="approachLead('${escapeHtml(lead.id)}')">✓ Apply & Quote</button>
        <a class="lead-link-btn" href="${escapeHtml(lead.approach_urls?.linkedin || lead.approach_urls?.linkedin_people || lead.url)}" target="_blank" rel="noopener">Find on LinkedIn ↗</a>
        <a class="lead-link-btn" href="${escapeHtml(lead.url)}" target="_blank" rel="noopener">View gig post ↗</a>
        <button type="button" class="btn btn-outline btn-sm" onclick="dismissLead('${escapeHtml(lead.id)}')">Dismiss</button>
      </div>
    </div>
  `).join('');
}

async function loadFreelancingView() {
  await refreshLiveLeads();
}

async function refreshLiveLeads() {
  try {
    const data = await api('/leads/live');
    renderLiveLeads({ status: data.status, items: data.leads });
  } catch {
    /* ignore poll errors */
  }
}

async function scanLeadsNow() {
  try {
    showToast('Scanning Reddit & freelance boards for paid gigs…', 'success');
    const result = await api('/leads/scan', { method: 'POST', body: '{}' });
    showToast(result.message || 'Scan complete', 'success');
    await refreshLiveLeads();
  } catch (err) {
    showToast(err.message || 'Scan failed');
  }
}

async function approachLead(leadId) {
  try {
    showToast('Sales team approaching client & building quotation…', 'success');
    const result = await api(`/leads/${leadId}/approach`, { method: 'POST', body: '{}' });
    showToast(result.message, 'success');
    await refreshLiveLeads();
    if (document.querySelector('.view.active')?.id === 'view-dashboard') {
      await loadDashboard();
    }
    if (result.project) openProject(result.project.id);
  } catch (err) {
    showToast(err.message || 'Could not approach lead');
  }
}

async function dismissLead(leadId) {
  try {
    await api(`/leads/${leadId}/dismiss`, { method: 'POST', body: '{}' });
    await refreshLiveLeads();
  } catch (err) {
    showToast(err.message);
  }
}

function renderInhouseWalkgether(wg) {
  const el = document.getElementById('inhouse-walkgether');
  if (!wg) {
    el.classList.add('hidden');
    return;
  }
  el.classList.remove('hidden');
  const mvpList = (wg.mvp_features || []).slice(0, 4).map(f => `<li>${escapeHtml(f)}</li>`).join('');
  const phaseBadge = wg.phase === 'mobile_app'
    ? '<span class="inhouse-phase">📱 Mobile App Phase</span>'
    : '<span class="inhouse-phase">🌐 Website Phase</span>';
  const teamHtml = wg.hired_mobile_team && wg.mobile_team?.length
    ? `<div class="inhouse-hires"><small>New hires:</small> ${wg.mobile_team.map(m => `<span class="hire-chip">${escapeHtml(m.name)} · ${escapeHtml(m.role)}</span>`).join('')}</div>`
    : '';
  el.innerHTML = `
    <div class="inhouse-header">
      <div>
        <span class="inhouse-badge">🏠 In-House Project</span>
        ${phaseBadge}
        <h3>🚶 ${escapeHtml(wg.title)}</h3>
        <p class="inhouse-tagline">${escapeHtml(wg.tagline)}</p>
        <p class="inhouse-desc">${escapeHtml(wg.description)}</p>
        ${teamHtml}
      </div>
      <div class="inhouse-actions">
        ${wg.app_preview_available ? `<button type="button" class="btn btn-success" onclick="openWalkgetherAppPreview()">📱 App Preview</button>` : ''}
        ${wg.preview_available ? `<button type="button" class="btn btn-outline btn-sm" onclick="openWalkgetherPreview()">🌐 Website</button>` : ''}
        <button type="button" class="btn btn-outline btn-sm" onclick="document.querySelector('[data-view=team]').click()">📹 Watch Team Build</button>
      </div>
    </div>
    <div class="inhouse-meta">
      <div class="inhouse-progress">
        <div class="progress-label"><span>${escapeHtml(wg.phase_label || 'Progress')}</span><strong>${wg.progress_percent}%</strong></div>
        <div class="progress-bar"><div class="progress-fill" style="width:${wg.progress_percent}%"></div></div>
        <small>${wg.tasks_completed} / ${wg.tasks_total} tasks · ${wg.files_count} files · Team: ${wg.team_size || 11}</small>
      </div>
      <ul class="inhouse-mvp">${mvpList}</ul>
    </div>
  `;
}

async function loadInhouseView() {
  try {
    const wg = await api('/inhouse/walkgether');
    renderInhouseWalkgether(wg);
  } catch (err) {
    const el = document.getElementById('inhouse-walkgether');
    el.classList.remove('hidden');
    el.innerHTML = `<div class="list-empty">Could not load Walkgether: ${escapeHtml(err.message)}</div>`;
  }
}

function openWalkgetherAppPreview() {
  currentPreviewId = 'walkgether-app';
  document.getElementById('preview-title').textContent = 'Walkgether App — Live';
  document.getElementById('preview-subtitle').textContent = 'Full working app · register, match, chat & schedule walks';
  document.getElementById('preview-frame').src = '/walkgether/app/';
  document.getElementById('preview-modal').classList.remove('hidden');
  closeModal();
}

function openWalkgetherPreview() {
  currentPreviewId = 'walkgether';
  document.getElementById('preview-title').textContent = 'Walkgether — In-House';
  document.getElementById('preview-subtitle').textContent = 'Walk Together. Stay Healthy. Build Connections.';
  document.getElementById('preview-frame').src = '/deliverables/inhouse/walkgether/index.html';
  document.getElementById('preview-modal').classList.remove('hidden');
  closeModal();
}

async function loadDashboard() {
  const data = await api('/dashboard');
  const s = data.stats;
  renderNotifications(data.notifications);

  document.getElementById('stats-grid').innerHTML = `
    <div class="stat-card"><div class="label">Total Projects</div><div class="value">${s.total_projects}</div></div>
    <div class="stat-card"><div class="label">Active</div><div class="value">${s.active_projects}</div></div>
    <div class="stat-card"><div class="label">Completed</div><div class="value">${s.completed_projects}</div></div>
    <div class="stat-card pending"><div class="label">Awaiting Your Approval</div><div class="value">${s.pending_approvals}</div></div>
    <div class="stat-card revenue"><div class="label">Revenue Received</div><div class="value">$${s.total_revenue.toLocaleString()}</div></div>
    <div class="stat-card"><div class="label">AI Team Size</div><div class="value">${s.team_size}</div></div>
  `;

  const projectsEl = document.getElementById('recent-projects');
  if (!data.recent_projects.length) {
    projectsEl.innerHTML = '<div class="list-empty">No projects yet. Open <strong>Freelancing</strong> to find gigs or click Demo Client.</div>';
  } else {
    projectsEl.innerHTML = data.recent_projects.map(p => renderProjectCard(p, { compact: true })).join('');
  }

  const actEl = document.getElementById('recent-activity');
  if (!data.recent_activity.length) {
    actEl.innerHTML = '<div class="list-empty">No activity yet.</div>';
  } else {
    actEl.innerHTML = data.recent_activity.slice(0, 8).map(a => `
      <div class="activity-item">
        <span class="time">${formatTime(a.created_at)}</span>
        <div><span class="agent">${a.agent_name}</span> — <span class="action">${a.action}</span></div>
      </div>
    `).join('');
  }
}

async function loadProjects() {
  const projects = await api('/projects');
  const el = document.getElementById('projects-list');
  if (!projects.length) {
    el.innerHTML = '<div class="list-empty">No projects. Create one to get started!</div>';
    return;
  }
  el.innerHTML = projects.map(p => renderProjectCard(p)).join('');
}

function renderWorkflow() {
  const stages = company.workflow_stages || Object.keys(STAGE_LABELS);
  document.getElementById('workflow-pipeline').innerHTML = stages.map((s, i) => {
    let cls = 'pipeline-step';
    if (s === 'ceo_approval') cls += ' ceo-step';
    if (s === 'payment_collection') cls += ' payment-step';
    return `<div class="${cls}"><div class="num">${i + 1}</div><div class="label">${formatStage(s)}</div></div>`;
  }).join('');

  document.getElementById('workflow-detail').innerHTML = WORKFLOW_DETAILS.map((d, i) => `
    <div class="step-detail">
      <div class="step-num">${i + 1}</div>
      <div>
        <h4>${d.title}</h4>
        <p>${d.desc}</p>
        <div class="agents">👥 ${d.agents}</div>
      </div>
    </div>
  `).join('');
}

async function loadActivity() {
  const logs = await api('/activity?limit=50');
  const el = document.getElementById('full-activity');
  if (!logs.length) {
    el.innerHTML = '<div class="list-empty">No activity logged yet.</div>';
    return;
  }
  el.innerHTML = logs.map(a => `
    <div class="activity-item">
      <span class="time">${new Date(a.created_at).toLocaleString()}</span>
      <div>
        <span class="agent">${a.agent_name}</span> (${a.agent_role.replace(/_/g, ' ')})
        — <span class="action">${a.action}</span>
        ${a.stage ? `<br><small style="color:var(--text-muted)">Stage: ${formatStage(a.stage)}</small>` : ''}
      </div>
    </div>
  `).join('');
}

async function openProject(id) {
  const data = await api(`/projects/${id}`);
  const p = data.project;
  const q = data.quotation;
  const pay = data.payment;
  const done = isProjectDone(p);
  const previewed = p.preview_available && isProjectPreviewed(id);
  const showDoneAlert = done && p.preview_available && !previewed;

  let actions = '';
  if (p.preview_available) {
    actions = previewButton(id, p.title, previewed ? 'View Again' : 'Live Preview', 'btn-success-inline');
  }
  if (p.current_stage === 'ceo_approval') {
    actions += `
      <button class="btn btn-success" onclick="ceoApprove(${id}, true)">✓ Approve Quotation</button>
      <button class="btn btn-danger" onclick="ceoApprove(${id}, false)">✗ Reject</button>
    `;
  } else if (!done) {
    actions += `
      <button class="btn btn-primary" onclick="runStage(${id})">▶ Run Next Stage</button>
      <button class="btn btn-outline" onclick="runAll(${id})">⏩ Run All Remaining</button>
    `;
  }

  let quotationHtml = '';
  if (q) {
    const rows = q.line_items.map(i =>
      `<tr><td>${i.item}</td><td>${i.hours || '-'}</td><td>$${i.rate || '-'}</td><td>$${i.amount.toLocaleString()}</td></tr>`
    ).join('');
    quotationHtml = `
      <div class="detail-section">
        <h3>Quotation ${q.approved_by_ceo ? '✓ Approved' : '(Pending CEO)'}</h3>
        <table class="quotation-table">
          <thead><tr><th>Item</th><th>Hours</th><th>Rate</th><th>Amount</th></tr></thead>
          <tbody>${rows}</tbody>
          <tfoot>
            <tr><td colspan="3">Subtotal</td><td>$${q.subtotal.toLocaleString()}</td></tr>
            <tr><td colspan="3">Tax (${q.tax_percent}%)</td><td>$${q.tax_amount.toLocaleString()}</td></tr>
            <tr class="total"><td colspan="3">Total</td><td>$${q.total_amount.toLocaleString()}</td></tr>
          </tfoot>
        </table>
        <p style="margin-top:0.5rem;font-size:0.85rem;color:var(--text-muted)">${q.notes}</p>
      </div>
    `;
  }

  let paymentHtml = '';
  if (pay) {
    paymentHtml = `
      <div class="detail-section">
        <h3>Payment — ${pay.status === 'received' ? '✓ Received' : 'Pending'}</h3>
        <p><strong>$${pay.amount.toLocaleString()}</strong> → ${pay.ceo_account}</p>
      </div>
    `;
  }

  let previewHtml = '';
  if (p.preview_available && !previewed) {
    previewHtml = `
      <div class="detail-section">
        <div class="live-preview-cta">
          <h3>✓ Project Delivered</h3>
          <p>Your AI team built this project. Click below to see how it looks live.</p>
          ${previewButton(id, p.title, 'Open Live Preview', 'preview-btn-lg')}
        </div>
      </div>
    `;
  }

  document.getElementById('project-detail').innerHTML = `
    <div class="detail-header">
      <h2>${escapeHtml(p.title)} ${showDoneAlert ? '<span class="done-ribbon" style="position:static;margin-left:0.5rem">✓ DONE</span>' : ''}</h2>
      <div class="client">${p.client_company} — ${p.client_name} (${p.client_email})</div>
      <span class="stage-badge ${stageBadgeClass(p.current_stage)}">${formatStage(p.current_stage)}</span>
    </div>
    <p style="margin-bottom:1rem;color:var(--text-muted)">${p.description}</p>
    <div class="detail-actions">${actions}</div>
    ${previewHtml}
    ${quotationHtml}
    ${paymentHtml}
    ${!done && p.requirements ? `<div class="detail-section"><h3>Requirements</h3><div class="detail-content">${escapeHtml(p.requirements)}</div></div>` : ''}
    ${!done && p.tech_stack ? `<div class="detail-section"><h3>Tech Stack</h3><div class="detail-content">${escapeHtml(p.tech_stack)}</div></div>` : ''}
    <div class="detail-section">
      <h3>Activity Timeline</h3>
      <div class="activity-feed">
        ${data.activity.map(a => `
          <div class="activity-item">
            <span class="time">${formatTime(a.created_at)}</span>
            <div><span class="agent">${a.agent_name}</span> — ${a.action}</div>
          </div>
        `).join('') || '<div class="list-empty">No activity</div>'}
      </div>
    </div>
  `;
  document.getElementById('project-modal').classList.remove('hidden');
}

function escapeHtml(text) {
  if (text == null) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

function escapeAttr(text) {
  return escapeHtml(String(text ?? ''));
}

function previewButton(id, title, label = 'Preview', extraClass = '') {
  return `<button type="button" class="preview-btn ${extraClass}" data-preview-id="${id}" data-preview-title="${escapeAttr(title)}"><span class="preview-btn-icon">👁</span> ${label}</button>`;
}

function openPreview(projectId, title) {
  currentPreviewId = projectId;
  markProjectPreviewed(projectId);
  document.getElementById('preview-title').textContent = title || 'Live Preview';
  document.getElementById('preview-subtitle').textContent = 'Real-time preview of the delivered project';
  document.getElementById('preview-frame').src = `/deliverables/${projectId}/index.html`;
  document.getElementById('preview-modal').classList.remove('hidden');
  closeModal();
}

function closePreview() {
  document.getElementById('preview-modal').classList.add('hidden');
  document.getElementById('preview-frame').src = 'about:blank';
  currentPreviewId = null;
}

function openPreviewNewTab() {
  if (currentPreviewId === 'walkgether-app') {
    window.open('/walkgether/app/', '_blank');
  } else if (currentPreviewId === 'walkgether') {
    window.open('/deliverables/inhouse/walkgether/index.html', '_blank');
  } else if (currentPreviewId) {
    window.open(`/deliverables/${currentPreviewId}/index.html`, '_blank');
  }
}

function closeModal() {
  document.getElementById('project-modal').classList.add('hidden');
}

function showNewProjectModal() {
  document.getElementById('new-project-modal').classList.remove('hidden');
}

function closeNewProjectModal() {
  document.getElementById('new-project-modal').classList.add('hidden');
}

async function createProject(e) {
  e.preventDefault();
  const form = e.target;
  const body = Object.fromEntries(new FormData(form));
  try {
    showToast('Starting AI pipeline...', 'success');
    closeNewProjectModal();
    const result = await api('/projects', { method: 'POST', body: JSON.stringify(body) });
    showToast(result.status === 'paused_at_ceo_approval'
      ? 'Pipeline paused — quotation needs your approval!'
      : 'Project created!', 'success');
    form.reset();
    await loadProjects();
    if (result.project) openProject(result.project.id);
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function simulateLead() {
  try {
    showToast('AI team finding new client...', 'success');
    const result = await api('/simulate-lead', { method: 'POST', body: '{}' });
    showToast(result.message, 'success');
    await loadDashboard();
    if (result.project) openProject(result.project.id);
  } catch (err) {
    showToast(err.message);
  }
}

async function runStage(id) {
  try {
    showToast('AI team working...', 'success');
    const result = await api(`/projects/${id}/run-stage`, { method: 'POST' });
    showToast(`Stage complete → ${formatStage(result.next_stage)}`, 'success');
    openProject(id);
    loadDashboard();
  } catch (err) {
    showToast(err.message || 'Request failed', 'danger');
  }
}

async function runAll(id) {
  try {
    showToast('Running pipeline — this may take 1-2 minutes...', 'success');
    const result = await api(`/projects/${id}/run-all`, { method: 'POST' });
    if (result.warning) showToast(result.warning, '');
    if (result.status === 'completed') {
      showToast('🎉 Project done! Click Preview to see the live site.', 'success');
      const p = result.project;
      if (p?.preview_available) setTimeout(() => openPreview(id, p.title), 600);
    } else {
      showToast('Pipeline finished', 'success');
    }
    openProject(id);
    loadDashboard();
    loadProjects();
  } catch (err) {
    showToast(err.message || 'Request failed', 'danger');
  }
}

async function ceoApprove(id, approved) {
  const notes = approved ? 'Approved — proceed with development' : prompt('Rejection reason:') || 'Rejected';
  try {
    const result = await api(`/projects/${id}/ceo-approve`, {
      method: 'POST',
      body: JSON.stringify({ approved, notes }),
    });
    showToast(approved ? 'Quotation approved! Development starting...' : 'Quotation rejected', approved ? 'success' : '');
    openProject(id);
    loadDashboard();
  } catch (err) {
    showToast(err.message);
  }
}

init();

document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-preview-id]');
  if (!btn) return;
  e.stopPropagation();
  e.preventDefault();
  openPreview(Number(btn.dataset.previewId), btn.dataset.previewTitle);
});
