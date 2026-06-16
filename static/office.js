/**
 * Virtual office — 8 hours/day per member, no fixed schedule; shows live activity.
 */
const OfficeSimulator = (() => {
  const DAILY_HOURS = 8 * 60;           // 8-hour quota in minutes
  const DAILY_HOURS_MS = DAILY_HOURS * 60000;
  const OFFICE_HOURS_LABEL = '8 hours per day';

  const POIS = {
    entrance: { x: 6, y: 92 },
    coffee: { x: 90, y: 14 },
    lounge: { x: 52, y: 78 },
    hallway: { x: 30, y: 55 },
  };

  const DESKS = [
    { x: 10, y: 22 }, { x: 24, y: 22 }, { x: 38, y: 22 }, { x: 52, y: 22 }, { x: 66, y: 22 },
    { x: 10, y: 42 }, { x: 24, y: 42 }, { x: 38, y: 42 }, { x: 52, y: 42 }, { x: 66, y: 42 },
    { x: 18, y: 62 }, { x: 38, y: 62 }, { x: 58, y: 62 },
  ];

  const ROLE_EMOJI_MAP = {
    sales: '💼', marketing: '📣', hr: '🧑‍💼', business_analyst: '📋',
    project_manager: '📌', frontend_developer: '🎨', backend_developer: '⚙️',
    fullstack_developer: '🔧', mobile_developer: '📱', app_developer: '📲',
    qa_tester: '🔍', finance: '💰', client_success: '🤝',
  };

  let container = null;
  let agentsEl = null;
  let clockEl = null;
  let phaseEl = null;
  let feedEl = null;
  let rosterEl = null;
  let agents = new Map();
  let members = [];
  let tickTimer = null;
  let running = false;
  let liveFeed = [];
  const feedDedup = new Map();

  function minsNow() {
    const n = new Date();
    return n.getHours() * 60 + n.getMinutes();
  }

  function todayKey() {
    return new Date().toDateString();
  }

  function hashStr(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) h = ((h << 5) - h) + s.charCodeAt(i) | 0;
    return Math.abs(h);
  }

  function formatDuration(totalMinutes) {
    const h = Math.floor(totalMinutes / 60);
    const m = totalMinutes % 60;
    if (h === 0) return `${m}m`;
    if (m === 0) return `${h}h`;
    return `${h}h ${m}m`;
  }

  function assignReadyMin(memberName) {
    const key = todayKey();
    const sorted = [...members].sort((a, b) => a.name.localeCompare(b.name));
    const index = Math.max(0, sorted.findIndex(m => m.name === memberName));
    const total = sorted.length || 1;
    const spread = total > 1 ? Math.floor((index / (total - 1)) * 180) : 90;
    const jitter = hashStr(`${memberName}|${key}`) % 20;
    return 8 * 60 + spread + jitter;
  }

  function workProgress(memberName) {
    const agent = agents.get(memberName);
    if (!agent || !agent.shiftStart) {
      return { loggedMin: 0, remainingMin: DAILY_HOURS, done: false, started: false, pct: 0 };
    }
    const elapsed = Math.min(Date.now() - agent.shiftStart, DAILY_HOURS_MS);
    const loggedMin = Math.floor(elapsed / 60000);
    const remainingMin = Math.max(0, DAILY_HOURS - loggedMin);
    const done = elapsed >= DAILY_HOURS_MS;
    return {
      loggedMin,
      remainingMin,
      done,
      started: true,
      pct: Math.min(100, Math.round((loggedMin / DAILY_HOURS) * 100)),
    };
  }

  function memberStatus(member, memberName) {
    const agent = agents.get(memberName);
    const progress = workProgress(memberName);
    if (progress.done) return { label: 'Done for today', present: false, key: 'done' };
    if (!progress.started) {
      const ready = agent && minsNow() >= agent.readyMin;
      return ready
        ? { label: 'Starting shift', present: true, key: 'starting' }
        : { label: 'Off duty', present: false, key: 'off' };
    }
    if (member.status === 'working') {
      return { label: 'Working', present: true, key: 'working' };
    }
    return { label: 'On site', present: true, key: 'present' };
  }

  function shouldBePresent(memberName) {
    return memberStatus(memberByName(memberName) || {}, memberName).present;
  }

  function ensureShiftStarted(agent) {
    if (!agent || agent.shiftStart || agent.shiftEnded) return;
    if (minsNow() < agent.readyMin) return;
    agent.shiftStart = Date.now();
  }

  function officePhase() {
    if (!members.length) return 'workday';
    const anyPresent = members.some(m => shouldBePresent(m.name));
    if (!anyPresent) return 'closed';
    const anyStarting = members.some(m => {
      const s = memberStatus(m, m.name);
      return s.key === 'starting';
    });
    if (anyStarting) return 'login';
    const anyFinishing = members.some(m => {
      const p = workProgress(m.name);
      return p.started && !p.done && p.remainingMin <= 15;
    });
    if (anyFinishing) return 'logout';
    return 'workday';
  }

  function phaseLabel(phase) {
    const labels = {
      closed: 'Office quiet — team on flexible 8-hour shifts',
      login: 'Team starting their shifts',
      workday: `Workday in progress — ${OFFICE_HOURS_LABEL}`,
      logout: 'Team wrapping up daily 8-hour shifts',
    };
    return labels[phase] || '';
  }

  function formatClock() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function formatTodayDate() {
    return new Date().toLocaleDateString([], {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  }

  function activitySummary(member) {
    const task = member.current_task || 'Standing by';
    const detail = clip(member.work_details, 120) || 'Ready for next assignment';
    const working = member.status === 'working';
    return { task, detail, working };
  }

  function firstName(name) {
    return (name || '').split(' ')[0];
  }

  function clip(text, max = 90) {
    if (!text) return '';
    return text.length > max ? `${text.slice(0, max)}…` : text;
  }

  function memberByName(name) {
    return members.find(m => m.name === name);
  }

  function workBubble(member) {
    const task = member.current_task || 'Working';
    const project = member.project_title || 'project';
    const details = clip(member.work_details, 70);
    if (member.status === 'working') {
      return {
        title: `🟢 ${task}`,
        detail: details || `Focused on ${project}`,
      };
    }
    return {
      title: `⚪ ${task}`,
      detail: details || `Last worked on ${project}`,
    };
  }

  function coffeeBubble(member) {
    return {
      title: '☕ Coffee break',
      detail: `Quick break — then back to ${member.project_title || member.current_task || 'desk'}`,
    };
  }

  function walkBubble(member) {
    return {
      title: '🚶 Moving around',
      detail: `Heading to ${member.project_title ? `check on ${member.project_title}` : 'another desk'}`,
    };
  }

  function dialogueLines(a, b) {
    const proj = a.project_title || b.project_title || 'Walkgether';
    return [
      { speaker: a.name, text: `Hey ${firstName(b.name)}, how's ${proj} going?` },
      { speaker: b.name, text: clip(b.work_details) || `I'm on "${b.current_task}" right now.` },
      { speaker: a.name, text: clip(a.work_details) || `Same here — "${a.current_task}".` },
      { speaker: b.name, text: `Let's sync after standup on ${proj}.` },
    ];
  }

  function addFeedEntry(type, agentName, message, extra = '') {
    const key = `${agentName}|${type}|${message}`;
    const now = Date.now();
    if (feedDedup.get(key) && now - feedDedup.get(key) < 10000) return;
    feedDedup.set(key, now);
    liveFeed.unshift({
      time: new Date(),
      type,
      agent: agentName,
      message,
      extra,
    });
    if (liveFeed.length > 40) liveFeed.length = 40;
    renderFeed();
  }

  function renderFeed() {
    if (!feedEl) return;
    if (!liveFeed.length) {
      feedEl.innerHTML = '<div class="list-empty">Office activity will appear here…</div>';
      return;
    }
    feedEl.innerHTML = liveFeed.map(entry => {
      const icon = { work: '💻', talk: '💬', coffee: '☕', walk: '🚶', login: '🚪', logout: '🚪' }[entry.type] || '•';
      return `
        <div class="office-feed-item office-feed-${entry.type}">
          <span class="office-feed-time">${entry.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          <div class="office-feed-body">
            <strong>${icon} ${escapeHtml(entry.agent)}</strong>
            <p>${escapeHtml(entry.message)}</p>
            ${entry.extra ? `<small>${escapeHtml(entry.extra)}</small>` : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  function renderRoster() {
    if (!rosterEl) return;
    rosterEl.innerHTML = members.map((m) => {
      const status = memberStatus(m, m.name);
      const progress = workProgress(m.name);
      const activity = activitySummary(m);
      const dotClass = status.present ? 'online' : 'offline';
      const statusClass = status.key === 'working' ? 'working' : status.key;
      return `
        <div class="office-roster-card ${m.status}${m.inhouse ? ' inhouse' : ''} ${status.present ? 'present' : 'absent'}">
          <div class="office-roster-top">
            <div class="office-roster-face-wrap">
              <img class="office-roster-face" src="${faceUrl(m.name)}" alt="" />
              <span class="office-presence-dot ${dotClass}" title="${status.label}"></span>
            </div>
            <div>
              <strong>${escapeHtml(m.name)}</strong>
              <small>${escapeHtml(m.department)}</small>
            </div>
            <span class="office-roster-status ${statusClass}">${status.label}</span>
          </div>
          <div class="office-roster-current">
            <span class="office-current-label">Currently doing</span>
            <p class="office-roster-task ${activity.working ? 'is-working' : ''}">${escapeHtml(activity.task)}</p>
            ${m.project_title ? `<p class="office-roster-project">📁 ${escapeHtml(m.project_title)}</p>` : ''}
            <p class="office-roster-detail">${escapeHtml(activity.detail)}</p>
            ${m.stage ? `<p class="office-roster-stage">Stage: ${escapeHtml(m.stage.replace(/_/g, ' '))}</p>` : ''}
          </div>
          <div class="office-daily-progress">
            <div class="office-daily-progress-head">
              <span>Daily quota</span>
              <span>${formatDuration(progress.loggedMin)} / 8h</span>
            </div>
            <div class="office-daily-progress-bar">
              <div class="office-daily-progress-fill" style="width:${progress.pct}%"></div>
            </div>
            <small class="office-daily-progress-note">${progress.done ? 'Shift complete' : `${formatDuration(progress.remainingMin)} remaining today`}</small>
          </div>
        </div>
      `;
    }).join('');
  }

  function updateOfficeStatusIndicators() {
    const phase = officePhase();
    const open = phase !== 'closed';

    const pageDot = document.querySelector('#view-office .live-dot');
    if (pageDot) {
      pageDot.classList.toggle('office-open', open);
      pageDot.classList.toggle('office-closed', !open);
    }

    const hdrDot = document.getElementById('office-status-dot');
    if (hdrDot) hdrDot.className = `office-status-dot ${open ? 'open' : 'closed'}`;

    const hdrLabel = document.getElementById('office-hours-status');
    if (hdrLabel) {
      hdrLabel.textContent = open ? 'Office open' : 'Office closed';
      hdrLabel.className = `office-hours-status ${open ? 'open' : 'closed'}`;
    }

    const liveLabel = document.getElementById('office-live-label');
    if (liveLabel) liveLabel.textContent = open ? 'OFFICE OPEN' : 'OFFICE CLOSED';

    const dateEl = document.getElementById('office-today-date');
    if (dateEl) dateEl.textContent = formatTodayDate();
  }

  function updateAgentPresence(agent, member) {
    const status = memberStatus(member, agent.id);
    const progress = workProgress(agent.id);
    const activity = activitySummary(member);
    const dot = agent.el.querySelector('.agent-presence-dot');
    if (dot) dot.className = `agent-presence-dot ${status.present ? 'online' : 'offline'}`;
    agent.el.classList.toggle('agent-present', status.present);
    agent.el.classList.toggle('agent-away', !status.present);
    agent.el.dataset.status = status.present ? 'present' : 'away';
    agent.el.style.zIndex = String(10 + (agent.labelOffset || 0));

    const activityEl = agent.el.querySelector('.agent-activity-tag');
    if (activityEl) {
      activityEl.textContent = activity.task;
      activityEl.classList.toggle('is-working', activity.working);
    }
    const hoursEl = agent.el.querySelector('.agent-hours-tag');
    if (hoursEl) {
      hoursEl.textContent = progress.started
        ? `${formatDuration(progress.loggedMin)} / 8h`
        : '8h shift';
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  function faceUrl(name) {
    return `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(name)}&backgroundColor=1a2234,2a3548,3b4f6a`;
  }

  function setBubble() {
    /* Bubbles hidden on floor — details live in side panel only */
  }

  function moveAgent(agent, x, y, state) {
    agent.x = x;
    agent.y = y;
    agent.state = state;
    const el = agent.el;
    if (!el) return;
    el.style.left = `${x}%`;
    el.style.top = `${y}%`;
    el.className = `office-agent state-${state}${agent.apiWorking ? ' api-working' : ''}`;
  }

  function pickIdleActivity(agent, allPresent) {
    const roll = Math.random();
    if (roll < 0.3) return { type: 'coffee', target: POIS.coffee };
    if (roll < 0.5) return { type: 'walk', target: POIS.hallway };
    if (roll < 0.72 && allPresent.length >= 2) {
      const buddy = allPresent.find(a => a.id !== agent.id && a.state !== 'talking');
      if (buddy) return { type: 'talking', target: POIS.lounge, buddy: buddy.id };
    }
    return { type: 'desk', target: agent.desk };
  }

  function tickAgent(agent, index, total, presentAgents) {
    const member = memberByName(agent.id);
    if (!member) return;

    ensureShiftStarted(agent);
    const progress = workProgress(agent.id);
    const present = shouldBePresent(agent.id) && !progress.done;

    if (progress.done && !agent.shiftEnded) {
      agent.shiftEnded = true;
    }

    if (!present) {
      if (agent.state !== 'away' && agent.state !== 'leaving') {
        moveAgent(agent, POIS.entrance.x, POIS.entrance.y, 'leaving');
        if (agent.checkedInToday) {
          addFeedEntry('logout', agent.id, `Finished 8-hour shift. Last task: ${member.current_task}`);
        }
        setTimeout(() => {
          moveAgent(agent, POIS.entrance.x, POIS.entrance.y + 10, 'away');
          agent.el.classList.add('fading-out');
        }, 1800);
      }
      return;
    }

    agent.el.classList.remove('fading-out');

    if ((agent.state === 'away' || agent.state === 'leaving') && present) {
      moveAgent(agent, agent.desk.x, agent.desk.y, 'working');
      if (!agent.checkedInToday) {
        addFeedEntry('login', agent.id, `Started shift — ${member.current_task}`);
        agent.checkedInToday = true;
      }
      return;
    }

    const workB = workBubble(member);
    if (agent.apiWorking || member.status === 'working') {
      moveAgent(agent, agent.desk.x, agent.desk.y, 'working');
      return;
    }

    if (agent.state === 'away') {
      moveAgent(agent, agent.desk.x, agent.desk.y, 'working');
      return;
    }

    if (agent.busyUntil && Date.now() < agent.busyUntil) {
      return;
    }

    const activity = pickIdleActivity(agent, presentAgents);
    agent.busyUntil = Date.now() + 5000 + Math.random() * 4000;

    if (activity.type === 'talking' && activity.buddy) {
      const buddy = agents.get(activity.buddy);
      const buddyMember = memberByName(activity.buddy);
      if (buddy && buddyMember) {
        const lines = dialogueLines(member, buddyMember);
        agent.dialogue = lines;
        buddy.dialogue = lines;
        agent.dialogueIndex = 0;
        buddy.dialogueIndex = 1;
        const ox = (Math.random() - 0.5) * 14 + (agent.labelOffset || 0) * 0.4;
        const oy = (buddy.labelOffset || 0) * 0.35;
        const line = lines[0];
        moveAgent(agent, POIS.lounge.x + ox, POIS.lounge.y + oy, 'talking');
        moveAgent(buddy, POIS.lounge.x - ox, POIS.lounge.y + 4 - oy, 'talking');
        buddy.busyUntil = agent.busyUntil;
        addFeedEntry('talk', agent.id, line.text, `Talking with ${buddy.id} about ${member.project_title || buddyMember.project_title || 'work'}`);
        addFeedEntry('talk', buddy.id, lines[1].text, `Reply to ${agent.id}`);
        return;
      }
    }

    if (activity.type === 'coffee') {
      const b = coffeeBubble(member);
      moveAgent(agent, POIS.coffee.x, POIS.coffee.y, 'coffee');
      addFeedEntry('coffee', agent.id, b.detail);
      return;
    }

    if (activity.type === 'walk') {
      const b = walkBubble(member);
      moveAgent(agent, POIS.hallway.x, POIS.hallway.y, 'walking');
      addFeedEntry('walk', agent.id, b.detail);
      return;
    }

    moveAgent(agent, agent.desk.x, agent.desk.y, 'working');
    addFeedEntry('work', agent.id, workB.title.replace(/^🟢 |^⚪ /, ''), workB.detail);
  }

  function renderFloor() {
    if (!container) return;
    const deskHtml = DESKS.map((d, i) => `
      <div class="office-desk" style="left:${d.x}%;top:${d.y}%">
        <div class="desk-surface"></div>
        <div class="desk-chair"></div>
      </div>
    `).join('');

    container.innerHTML = `
      <div class="office-layout-full">
        <div class="office-wrap office-wrap-full">
          <div class="office-header-bar">
            <div>
              <div class="office-title-row">
                <span id="office-status-dot" class="office-status-dot closed"></span>
                <strong>🏢 AI Nexus Office</strong>
              </div>
              <span id="office-today-date" class="office-today-date"></span>
              <span id="office-phase-label" class="office-phase-label"></span>
            </div>
            <div class="office-clock-wrap">
              <div class="office-hours-status-row">
                <span id="office-hours-status" class="office-hours-status closed">Office closed</span>
              </div>
              <span class="office-hours">${OFFICE_HOURS_LABEL}</span>
              <span id="office-clock" class="office-clock">--:--</span>
            </div>
          </div>
          <div class="office-floor office-floor-full">
            <div class="office-zone office-zone-entrance">🚪 Entrance</div>
            <div class="office-zone office-zone-coffee">☕ Coffee Bar</div>
            <div class="office-zone office-zone-lounge">💬 Lounge</div>
            <div class="office-zone office-zone-dev">💻 Dev Floor</div>
            ${deskHtml}
            <div id="office-agents" class="office-agents"></div>
          </div>
        </div>
        <div class="office-bottom-panels">
          <div class="office-panel-section">
            <h3>💬 Live conversations & work</h3>
            <div id="office-live-feed" class="office-live-feed"></div>
          </div>
          <div class="office-panel-section">
            <h3>👥 What everyone is doing</h3>
            <div id="office-roster" class="office-roster"></div>
          </div>
        </div>
      </div>
    `;
    agentsEl = document.getElementById('office-agents');
    clockEl = document.getElementById('office-clock');
    phaseEl = document.getElementById('office-phase-label');
    feedEl = document.getElementById('office-live-feed');
    rosterEl = document.getElementById('office-roster');
  }

  function ensureAgent(member, index) {
    const id = member.name;
    let agent = agents.get(id);
    const desk = DESKS[index % DESKS.length];

    if (!agent) {
      const el = document.createElement('div');
      el.className = 'office-agent state-away';
      el.innerHTML = `
        <div class="agent-shadow"></div>
        <div class="agent-body">
          <img class="agent-face" src="${faceUrl(member.name)}" alt="${escapeHtml(member.name)}" />
          <span class="agent-presence-dot offline"></span>
        </div>
        <div class="agent-label-stack">
          <div class="agent-name-tag">${escapeHtml(firstName(member.name))}</div>
          <div class="agent-activity-tag">Standing by</div>
          <div class="agent-hours-tag">8h shift</div>
        </div>
      `;
      agentsEl.appendChild(el);
      agent = {
        id, el, desk,
        x: POIS.entrance.x, y: POIS.entrance.y,
        state: 'away', busyUntil: 0, apiWorking: false,
        readyMin: assignReadyMin(id),
        shiftStart: null,
        shiftEnded: false,
        labelOffset: index % 5,
      };
      agents.set(id, agent);
    }

    agent.apiWorking = member.status === 'working';
    agent.el.title = `${member.name}\n${member.current_task}\n${member.work_details || ''}`;
    updateAgentPresence(agent, member);
    return agent;
  }

  function tick() {
    if (!running) return;
    resetDailyCheckins();
    const phase = officePhase();
    if (clockEl) clockEl.textContent = formatClock();
    if (phaseEl) phaseEl.textContent = phaseLabel(phase);
    const wrap = container?.querySelector('.office-wrap');
    if (wrap) wrap.classList.toggle('office-closed', phase === 'closed');

    const present = members
      .map(m => agents.get(m.name))
      .filter(agent => agent && shouldBePresent(agent.id));

    members.forEach((m, i) => {
      const agent = agents.get(m.name);
      if (agent) {
        agent.dialogueIndex = (agent.dialogueIndex || 0) + 1;
        tickAgent(agent, i, members.length, present);
        updateAgentPresence(agent, m);
      }
    });

    updateOfficeStatusIndicators();
    renderRoster();
  }

  function sync(membersData) {
    if (!container) return;
    members = membersData || [];
    if (!agentsEl) renderFloor();
    members.forEach((m, i) => ensureAgent(m, i));
    agents.forEach((agent, name) => {
      if (!members.find(m => m.name === name)) {
        agent.el.remove();
        agents.delete(name);
      }
    });
    renderRoster();
    tick();
  }

  function start(containerId) {
    container = document.getElementById(containerId);
    if (!container) return;
    stop();
    running = true;
    agents.clear();
    members = [];
    liveFeed = [];
    feedDedup.clear();
    renderFloor();
    tickTimer = setInterval(tick, 2800);
    tick();
  }

  function resetDailyCheckins() {
    const today = todayKey();
    if (resetDailyCheckins._day !== today) {
      resetDailyCheckins._day = today;
      agents.forEach(a => {
        a.checkedInToday = false;
        a.shiftStart = null;
        a.shiftEnded = false;
        a.readyMin = assignReadyMin(a.id);
      });
    }
  }

  function stop() {
    running = false;
    if (tickTimer) {
      clearInterval(tickTimer);
      tickTimer = null;
    }
  }

  return { start, stop, sync, officePhase };
})();
