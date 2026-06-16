/**
 * Virtual office — 10:00 AM–6:15 PM with staggered arrival and departure.
 * Isometric floor plan (primary) matching labeled room layout.
 */
const OfficeSimulator = (() => {
  const USE_3D_OFFICE = true;

  const DAILY_HOURS = 8 * 60;
  const DAILY_HOURS_MS = DAILY_HOURS * 60000;

  const OFFICE_OPEN = 10 * 60;
  const OFFICE_CLOSE = 18 * 60 + 15;
  const ENTRY_WINDOW_START = 9 * 60 + 55;
  const ENTRY_WINDOW_END = 10 * 60 + 15;
  const EXIT_WINDOW_START = 18 * 60 + 5;
  const EXIT_WINDOW_END = 18 * 60 + 25;
  const OFFICE_HOURS_LABEL = '10:00 AM – 6:15 PM';

  const POIS = {
    entrance: { x: 11, y: 90 },
    coffee: { x: 86, y: 18 },
    lounge: { x: 11, y: 48 },
    hallway: { x: 11, y: 48 },
  };

  const DESKS = buildDeskGrid();

  const COFFEE_SLOTS = [
    { x: 78, y: 12 }, { x: 86, y: 16 }, { x: 92, y: 12 }, { x: 82, y: 24 }, { x: 90, y: 28 },
  ];

  const PHONE_SLOTS = [
    { x: 80, y: 72 }, { x: 90, y: 76 },
  ];

  const CHILL_SLOTS = [
    { x: 10, y: 12 }, { x: 16, y: 16 }, { x: 8, y: 20 },
  ];

  // Chill room slots — world coords aligned to 3D props (floor 24×18)
  function worldSlot(wx, wz) {
    return { x: (wx / 24) * 100, y: (wz / 18) * 100 };
  }

  const GAME_SLOTS = {
    chess: [{ x: 8, y: 14 }, { x: 14, y: 12 }],
    pool: [{ x: 12, y: 18 }],
    pingpong: [{ x: 16, y: 16 }],
    console: [{ x: 10, y: 10 }, { x: 14, y: 10 }, { x: 12, y: 14 }],
  };

  const LOUNGE_SLOTS = [
    { x: 8, y: 42 }, { x: 14, y: 46 }, { x: 10, y: 52 }, { x: 16, y: 54 },
  ];

  const HALLWAY_SLOTS = [
    { x: 38, y: 82 }, { x: 50, y: 86 }, { x: 62, y: 82 },
  ];

  function buildDeskGrid() {
    const rows = ['A', 'B', 'C', 'D', 'E'];
    const cols = [1, 2, 3, 4, 5];
    const startX = 32;
    const startY = 22;
    const gapX = 7.2;
    const gapY = 11.5;
    const desks = [];
    rows.forEach((row, ri) => {
      cols.forEach((col, ci) => {
        desks.push({
          id: `${row}${col}`,
          x: startX + ci * gapX,
          y: startY + ri * gapY,
        });
      });
    });
    return desks;
  }

  function deskIndexFor(memberName) {
    const sorted = [...members].sort((a, b) => a.name.localeCompare(b.name));
    const index = sorted.findIndex((m) => m.name === memberName);
    return index >= 0 ? index : 0;
  }

  function deskForMember(memberName) {
    return DESKS[deskIndexFor(memberName) % DESKS.length];
  }

  function slotFor(agent, slots) {
    const idx = (agent.deskIndex ?? 0) % slots.length;
    return slots[idx];
  }

  function normalizeGameKey(game) {
    const g = (game || '').toLowerCase().trim();
    if (!g) return 'default';
    if (g.includes('fifa') || g.includes('fc 2') || g.includes('mario') || g.includes('kart')
      || g.includes('ps5') || g.includes('console') || g.includes('cod')
      || g.includes('fortnite') || g.includes('nba')) {
      return 'console';
    }
    if (g.includes('chess')) return 'chess';
    if (g.includes('pool') || g.includes('billiard') || g.includes('snooker')) return 'pool';
    if (g.includes('tennis') || g.includes('ping') || g.includes('pong')) return 'pingpong';
    return 'default';
  }

  function parseGameName(member) {
    if (member.office_game) return member.office_game;
    const task = member.current_task || '';
    const playing = task.match(/playing\s+(.+)/i);
    if (playing) return playing[1].trim();
    if (member.office_activity === 'gaming') {
      const details = member.work_details || '';
      const atGame = details.match(/At the (.+?)[\s.—]/i);
      if (atGame) return atGame[1].trim();
    }
    return '';
  }

  function gameSlotFor(agent, member) {
    const key = normalizeGameKey(parseGameName(member));
    const slots = GAME_SLOTS[key] || CHILL_SLOTS;
    return slotFor(agent, slots);
  }

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
  let scene3d = null;
  let scene3dReady = null;
  let povMember = null;

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

  function formatScheduleTime(totalMinutes) {
    const h = Math.floor(totalMinutes / 60);
    const m = totalMinutes % 60;
    const period = h >= 12 ? 'PM' : 'AM';
    const h12 = h % 12 || 12;
    return `${h12}:${String(m).padStart(2, '0')} ${period}`;
  }

  function todayAtMs(totalMinutes) {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d.getTime() + totalMinutes * 60000;
  }

  function formatWorkedTime(ms) {
    const totalMin = Math.floor(ms / 60000);
    if (totalMin <= 0) return '0m';
    return formatDuration(totalMin);
  }

  function assignEntryMin(memberName) {
    const key = todayKey();
    const windowMins = ENTRY_WINDOW_END - ENTRY_WINDOW_START;
    const sorted = [...members].sort((a, b) => a.name.localeCompare(b.name));
    const index = Math.max(0, sorted.findIndex(m => m.name === memberName));
    const total = sorted.length || 1;
    const slot = total > 1 ? Math.floor((index / (total - 1)) * windowMins) : Math.floor(windowMins / 2);
    const jitter = hashStr(`${memberName}|entry|${key}`) % 3;
    return ENTRY_WINDOW_START + slot + jitter;
  }

  function assignLeaveMin(memberName) {
    const key = todayKey();
    const windowMins = EXIT_WINDOW_END - EXIT_WINDOW_START;
    const sorted = [...members].sort((a, b) => a.name.localeCompare(b.name));
    const index = Math.max(0, sorted.findIndex(m => m.name === memberName));
    const total = sorted.length || 1;
    const slot = total > 1 ? Math.floor((index / (total - 1)) * windowMins) : Math.floor(windowMins / 2);
    const jitter = hashStr(`${memberName}|exit|${key}`) % 4;
    return EXIT_WINDOW_START + slot + jitter;
  }

  function workProgress(memberName) {
    const agent = agents.get(memberName);
    const nowMin = minsNow();
    if (!agent || nowMin < agent.entryMin) {
      return { loggedMin: 0, loggedMs: 0, remainingMin: DAILY_HOURS, done: false, started: false, pct: 0 };
    }

    const effectiveLeaveMin = Math.min(agent.leaveMin, OFFICE_CLOSE);
    const startMs = todayAtMs(agent.entryMin);
    const endMs = Math.min(Date.now(), todayAtMs(effectiveLeaveMin));
    const elapsedMs = Math.min(Math.max(0, endMs - startMs), DAILY_HOURS_MS);
    const loggedMin = Math.floor(elapsedMs / 60000);
    const remainingMin = Math.max(0, DAILY_HOURS - loggedMin);
    const done = nowMin >= effectiveLeaveMin || elapsedMs >= DAILY_HOURS_MS;
    const started = nowMin >= agent.entryMin && nowMin < effectiveLeaveMin;

    return {
      loggedMin,
      loggedMs: elapsedMs,
      remainingMin,
      done,
      started,
      pct: Math.min(100, Math.round((elapsedMs / DAILY_HOURS_MS) * 100)),
    };
  }

  function memberStatus(member, memberName) {
    const agent = agents.get(memberName);
    const now = minsNow();
    const entryMin = agent?.entryMin ?? ENTRY_WINDOW_START;
    const leaveMin = agent?.leaveMin ?? EXIT_WINDOW_END;

    if (now < entryMin) {
      return { label: 'Off duty', present: false, key: 'off' };
    }
    if (now >= OFFICE_CLOSE) {
      return { label: 'Left for today', present: false, key: 'done' };
    }
    if (now >= leaveMin) {
      return { label: 'Left for today', present: false, key: 'done' };
    }
    if (now < ENTRY_WINDOW_END && now >= entryMin && agent && !agent.checkedInToday) {
      return { label: 'Arriving', present: true, key: 'starting' };
    }
    if (now >= EXIT_WINDOW_START && now < leaveMin) {
      return { label: 'Wrapping up', present: true, key: 'leaving' };
    }
    if (member.office_activity === 'coffee') {
      return { label: 'Coffee break', present: true, key: 'coffee' };
    }
    if (member.office_activity === 'query') {
      return { label: 'Team Q&A', present: true, key: 'query' };
    }
    if (member.office_activity === 'phone') {
      return { label: 'On a call', present: true, key: 'phone' };
    }
    if (member.office_activity === 'gaming') {
      return { label: 'Games room', present: true, key: 'gaming' };
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
    if (!agent || agent.shiftEnded) return;
    if (minsNow() < agent.entryMin) return;
    if (!agent.shiftStart) {
      agent.shiftStart = todayAtMs(agent.entryMin);
    }
  }

  function isOfficeOpenNow() {
    const now = minsNow();
    return now >= ENTRY_WINDOW_START && now < OFFICE_CLOSE;
  }

  function officePhase() {
    const now = minsNow();
    if (now < ENTRY_WINDOW_START || now >= OFFICE_CLOSE) return 'closed';
    if (now < ENTRY_WINDOW_END) return 'login';
    if (now >= EXIT_WINDOW_START) return 'logout';
    return 'workday';
  }

  function phaseLabel(phase) {
    const labels = {
      closed: `Office closed — opens ${formatScheduleTime(OFFICE_OPEN)}`,
      login: `Team arriving (${formatScheduleTime(ENTRY_WINDOW_START)} – ${formatScheduleTime(ENTRY_WINDOW_END)})`,
      workday: `Workday in progress — ${OFFICE_HOURS_LABEL}`,
      logout: `Team leaving (${formatScheduleTime(EXIT_WINDOW_START)} – ${formatScheduleTime(OFFICE_CLOSE)})`,
    };
    return labels[phase] || '';
  }

  function formatClock() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function localTimePeriod() {
    const hour = new Date().getHours();
    if (hour >= 21 || hour < 6) return 'night';
    if (hour < 12) return 'morning';
    if (hour < 17) return 'noon';
    return 'evening';
  }

  const TIME_OF_DAY_LABELS = {
    night: '🌙 Night',
    morning: '🌅 Morning',
    noon: '☀️ Afternoon',
    evening: '🌆 Evening',
  };

  function applyLocalTimeTheme() {
    const period = localTimePeriod();
    const periods = ['night', 'morning', 'noon', 'evening'];
    const floor = container?.querySelector('.office-floor');
    const wrap = container?.querySelector('.office-wrap');
    [floor, wrap].forEach((el) => {
      if (!el) return;
      periods.forEach((p) => el.classList.remove(`office-time-${p}`));
      el.classList.add(`office-time-${period}`);
      el.setAttribute('data-time-period', period);
    });
    const badge = document.getElementById('office-time-of-day');
    const tzEl = document.getElementById('office-timezone');
    if (badge) badge.textContent = TIME_OF_DAY_LABELS[period] || period;
    if (tzEl) {
      try {
        tzEl.textContent = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Local';
      } catch {
        tzEl.textContent = 'Local time';
      }
    }
    scene3d?.applyTimeOfDay?.(period);
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
    if (member.office_activity === 'coffee') {
      return {
        task: 'Coffee break',
        detail: member.work_details || 'At the coffee bar',
        working: false,
      };
    }
    if (member.office_activity === 'query') {
      return {
        task: member.current_task || 'Team Q&A',
        detail: member.work_details || (member.conversation_partner
          ? `Talking with ${member.conversation_partner}`
          : 'In the lounge'),
        working: false,
      };
    }
    if (member.office_activity === 'phone') {
      return {
        task: member.current_task || 'On a call',
        detail: member.work_details || 'In the call room.',
        working: false,
      };
    }
    if (member.office_activity === 'gaming') {
      return {
        task: member.current_task || 'Games room',
        detail: member.work_details || 'Chilling and playing games.',
        working: false,
      };
    }
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

  function showMemberCard(member, agent) {
    const card = document.getElementById('office-member-card');
    if (!card) return;
    if (!member) {
      card.classList.add('hidden');
      return;
    }
    const status = memberStatus(member, member.name);
    const deskId = agent?.desk?.id || '—';
    const dotClass = status.present ? 'online' : 'offline';
    card.classList.remove('hidden');
    card.innerHTML = `
      <div class="omc-avatar">
        <img src="${faceUrl(member.name)}" alt="" />
        <span class="omc-dot ${dotClass}"></span>
      </div>
      <div class="omc-body">
        <strong>${escapeHtml(firstName(member.name))}</strong>
        <span class="omc-status">${escapeHtml(status.label)}</span>
        <span class="omc-desk">Desk · ${escapeHtml(deskId)}</span>
      </div>
      <button type="button" class="omc-close" aria-label="Close">&times;</button>
    `;
    card.querySelector('.omc-close')?.addEventListener('click', (e) => {
      e.stopPropagation();
      clearMemberPov();
    });
    document.querySelectorAll('.iso-desk').forEach((el) => {
      el.classList.toggle('is-focus', el.dataset.deskId === deskId);
    });
  }

  function setPovHighlight(name) {
    povMember = name || null;
    rosterEl?.querySelectorAll('[data-agent]').forEach((el) => {
      el.classList.toggle('is-pov-focus', !!name && el.dataset.agent === name);
    });
    agents.forEach((agent, id) => {
      agent.el?.classList.toggle('is-focus', !!name && id === name);
    });
    if (!name) {
      document.querySelectorAll('.iso-desk').forEach((el) => el.classList.remove('is-focus'));
      document.getElementById('office-member-card')?.classList.add('hidden');
    }
  }

  function focusMember(name) {
    const member = memberByName(name);
    const agent = agents.get(name);
    if (!member || !agent) return;
    setPovHighlight(name);
    showMemberCard(member, agent);
    if (scene3d) {
      let gameKey = null;
      if (member.office_activity === 'gaming' || agent.state === 'gaming') {
        const key = normalizeGameKey(parseGameName(member));
        if (key !== 'default') gameKey = key;
      }
      scene3d.focusOnCharacter(name, { state: agent.state, gameKey });
    }
  }

  function clearMemberPov() {
    setPovHighlight(null);
    scene3d?.clearCharacterPov();
  }

  function renderRoster() {
    if (!rosterEl) return;
    rosterEl.innerHTML = members.map((m) => {
      const status = memberStatus(m, m.name);
      const progress = workProgress(m.name);
      const activity = activitySummary(m);
      const agent = agents.get(m.name);
      const dotClass = status.present ? 'online' : 'offline';
      const statusClass = status.key === 'working' ? 'working' : status.key;
      const scheduleNote = agent
        ? `🕐 ${formatScheduleTime(agent.entryMin)} – ${formatScheduleTime(agent.leaveMin)}`
        : '';
      return `
        <div class="office-roster-card ${m.status}${m.inhouse ? ' inhouse' : ''} ${status.present ? 'present' : 'absent'}${povMember === m.name ? ' is-pov-focus' : ''}" data-agent="${escapeHtml(m.name)}" role="button" tabindex="0" title="View ${escapeHtml(firstName(m.name))}'s POV">
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
              <span>${formatWorkedTime(progress.loggedMs)} / 8h</span>
            </div>
            <div class="office-daily-progress-bar">
              <div class="office-daily-progress-fill" style="width:${progress.pct}%"></div>
            </div>
            <small class="office-daily-progress-note">${progress.done ? 'Shift complete' : progress.started ? `${formatWorkedTime(progress.loggedMs)} worked · ${formatDuration(progress.remainingMin)} left` : `Starts ${agent ? formatScheduleTime(agent.entryMin) : ''}`}</small>
            ${scheduleNote ? `<small class="office-schedule-note">${scheduleNote}</small>` : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  function updateOfficeStatusIndicators() {
    const phase = officePhase();
    const open = isOfficeOpenNow();

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

  async function waitForLayout(el) {
    for (let i = 0; i < 40; i++) {
      const parent = el.parentElement;
      const w = Math.max(el.clientWidth, parent?.clientWidth || 0);
      const h = Math.max(el.clientHeight, parent?.clientHeight || 0);
      if (w >= 40 && h >= 40) return;
      await new Promise((r) => requestAnimationFrame(r));
    }
  }

  function enable2DFallback() {
    document.getElementById('office-iso-floor')?.classList.remove('hidden-behind-3d');
    agentsEl = document.getElementById('office-agents');
  }

  function buildIsometricFloorHtml() {
    const deskHtml = DESKS.map((d) => `
      <div class="iso-desk" data-desk-id="${d.id}">
        <div class="iso-desk-chair"></div>
        <div class="iso-desk-surface">
          <div class="iso-desk-monitor"></div>
          <div class="iso-desk-keyboard"></div>
          <div class="iso-desk-plant"></div>
        </div>
        <span class="iso-desk-id">${d.id}</span>
      </div>
    `).join('');

    return `
      <div id="office-iso-floor" class="office-iso-floor">
        <div class="office-iso-viewport">
          <div class="office-iso-stage">
            <div class="office-iso-map">
              <div class="iso-room iso-room-gaming">
                <div class="iso-room-floor"></div>
                <div class="iso-gaming-tv"></div>
                <div class="iso-gaming-couch"></div>
                <div class="iso-gaming-stand"></div>
              </div>
              <div class="iso-room iso-room-meeting">
                <div class="iso-room-floor"></div>
                <div class="iso-meeting-table"></div>
                <div class="iso-meeting-chair iso-chair-1"></div>
                <div class="iso-meeting-chair iso-chair-2"></div>
                <div class="iso-meeting-chair iso-chair-3"></div>
                <div class="iso-meeting-chair iso-chair-4"></div>
                <div class="iso-meeting-chair iso-chair-5"></div>
                <div class="iso-meeting-chair iso-chair-6"></div>
              </div>
              <div class="iso-room iso-room-entrance">
                <div class="iso-room-floor"></div>
                <div class="iso-entrance-doors"></div>
                <div class="iso-entrance-mat"></div>
              </div>
              <div class="iso-room iso-room-dev">
                <div class="iso-room-floor"></div>
                <div class="iso-dev-desks">${deskHtml}</div>
              </div>
              <div class="iso-room iso-room-coffee">
                <div class="iso-room-floor"></div>
                <div class="iso-coffee-counter"></div>
                <div class="iso-coffee-machine"></div>
                <div class="iso-coffee-table iso-ct-1"><span></span><span></span><span></span><span></span></div>
                <div class="iso-coffee-table iso-ct-2"><span></span><span></span><span></span><span></span></div>
                <div class="iso-coffee-table iso-ct-3"><span></span><span></span><span></span><span></span></div>
                <div class="iso-coffee-table iso-ct-4"><span></span><span></span><span></span><span></span></div>
              </div>
              <div class="iso-room iso-room-calls">
                <div class="iso-room-floor"></div>
                <div class="iso-call-booth iso-booth-1"><div class="iso-booth-glass"></div><div class="iso-booth-desk"></div></div>
                <div class="iso-call-booth iso-booth-2"><div class="iso-booth-glass"></div><div class="iso-booth-desk"></div></div>
              </div>
              <div id="office-agents" class="office-agents office-iso-agents"></div>
            </div>
          </div>
          <div class="office-iso-pills">
            <span class="iso-pill iso-pill-gaming">🎮 Gaming Room</span>
            <span class="iso-pill iso-pill-meeting">🤝 Meeting Room</span>
            <span class="iso-pill iso-pill-entrance">🚪 Main Entrance</span>
            <span class="iso-pill iso-pill-dev">💻 Dev Floor</span>
            <span class="iso-pill iso-pill-coffee">☕ Coffee Break Room</span>
            <span class="iso-pill iso-pill-calls">📞 Call Booths</span>
          </div>
        </div>
      </div>
    `;
  }

  function build2DFloorHtml() {
    return buildIsometricFloorHtml();
  }

  function officeMemberCardHtml() {
    return '<div id="office-member-card" class="office-member-card hidden" aria-live="polite"></div>';
  }

  async function initScene3D(wrapEl) {
    if (!USE_3D_OFFICE) {
      enable2DFallback();
      return null;
    }
    if (!wrapEl) {
      enable2DFallback();
      return null;
    }
    wrapEl.innerHTML = '<div class="office-3d-loading">Loading 3D office…</div>';
    await waitForLayout(wrapEl);
    try {
      const mod = await import('/static/office3d.js');
      wrapEl.innerHTML = '';
      if (scene3d) scene3d.dispose();
      scene3d = new mod.Office3DScene(wrapEl);
      scene3d.buildDesks(DESKS);
      scene3d.onMemberClick = (name) => focusMember(name);
      scene3d.onPovExit = () => clearMemberPov();
      scene3d.onTimeOfDayChange = (period) => {
        const badge = document.getElementById('office-time-of-day');
        if (badge) badge.textContent = TIME_OF_DAY_LABELS[period] || period;
      };
      document.getElementById('office-iso-floor')?.classList.add('hidden-behind-3d');
      return scene3d;
    } catch (err) {
      console.error('3D office failed:', err);
      wrapEl.innerHTML = '';
      const floor = container?.querySelector('.office-floor');
      if (floor && !document.getElementById('office-iso-floor')) {
        floor.insertAdjacentHTML('afterbegin', buildIsometricFloorHtml());
        const legend = floor.querySelector('.office-3d-legend');
        if (legend) legend.className = 'office-iso-legend';
        floor.classList.remove('office-floor-3d-mode');
        floor.classList.add('office-floor-iso-mode');
      }
      enable2DFallback();
      return null;
    }
  }

  function hoursTextFor(agent, progress) {
    const nowMin = minsNow();
    if (progress.started) return `${formatWorkedTime(progress.loggedMs)} / 8h`;
    if (nowMin < agent.entryMin) return `In ${formatScheduleTime(agent.entryMin)}`;
    if (progress.done) return `Done · ${formatWorkedTime(progress.loggedMs)}`;
    return `${formatScheduleTime(agent.entryMin)} – ${formatScheduleTime(agent.leaveMin)}`;
  }

  function updateAgentPresence(agent, member) {
    const status = memberStatus(member, agent.id);
    const progress = workProgress(agent.id);
    const activity = activitySummary(member);
    const hoursText = hoursTextFor(agent, progress);

    if (scene3d) {
      scene3d.upsertCharacter(agent.id, member);
      scene3d.updateCharacter(agent.id, member, progress, activity, hoursText);
      scene3d.setCharacterVisible(agent.id, status.present);
      return;
    }

    if (!agent.el) return;

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
      const nowMin = minsNow();
      if (progress.started) {
        hoursEl.textContent = `${formatWorkedTime(progress.loggedMs)} / 8h`;
        hoursEl.title = `${progress.pct}% of daily quota`;
      } else if (nowMin < agent.entryMin) {
        hoursEl.textContent = `In ${formatScheduleTime(agent.entryMin)}`;
      } else if (progress.done) {
        hoursEl.textContent = `Done · ${formatWorkedTime(progress.loggedMs)}`;
      } else {
        hoursEl.textContent = `${formatScheduleTime(agent.entryMin)} – ${formatScheduleTime(agent.leaveMin)}`;
      }
    }
    const hoursFill = agent.el.querySelector('.agent-hours-fill');
    if (hoursFill) {
      hoursFill.style.width = `${progress.pct}%`;
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

  function moveAgent(agent, x, y, state, member) {
    agent.x = x;
    agent.y = y;
    agent.state = state;

    const visualState = state === 'idle' ? 'idle' : state;
    if (scene3d) {
      const mapState = {
        coffee: 'coffee',
        talking: 'talking',
        walking: 'walking',
        working: 'working',
        idle: 'idle',
        phone: 'phone',
        gaming: 'gaming',
      };
      const hints = {};
      if (member && (state === 'gaming' || member.office_activity === 'gaming')) {
        const key = normalizeGameKey(parseGameName(member));
        if (key !== 'default') hints.gameKey = key;
      }
      scene3d.moveCharacter(
        agent.id,
        x,
        y,
        mapState[visualState] || visualState,
        hints,
      );
      return;
    }

    const el = agent.el;
    if (!el) return;
    el.style.left = `${x}%`;
    el.style.top = `${y}%`;
    const seated = state === 'working' || state === 'idle';
    const depthZ = Math.round(8 + (y / 100) * 32);
    el.style.zIndex = String(10 + Math.round(y));
    el.style.setProperty('--depth-z', `${depthZ}px`);
    el.className = `office-agent state-${state}${agent.apiWorking ? ' api-working' : ''}${seated ? ' at-seat' : ''}`;
  }

  function zonePosition(zone, agent, member) {
    if (member.status === 'working' || zone === 'desk') {
      const querying = member.office_activity === 'query';
      return {
        x: agent.desk.x,
        y: agent.desk.y,
        state: member.status === 'working' ? 'working' : (querying ? 'talking' : 'idle'),
      };
    }
    if (zone === 'coffee' || zone === 'coffee_room') {
      const slot = slotFor(agent, COFFEE_SLOTS);
      return { x: slot.x, y: slot.y, state: 'coffee' };
    }
    if (zone === 'phone_room') {
      const slot = slotFor(agent, PHONE_SLOTS);
      return { x: slot.x, y: slot.y, state: 'phone' };
    }
    if (zone === 'chill_room') {
      const slot = gameSlotFor(agent, member);
      return { x: slot.x, y: slot.y, state: 'gaming' };
    }
    if (zone === 'lounge') {
      const slot = slotFor(agent, LOUNGE_SLOTS);
      return { x: slot.x, y: slot.y, state: 'talking' };
    }
    if (zone === 'hallway') {
      const slot = slotFor(agent, HALLWAY_SLOTS);
      return { x: slot.x, y: slot.y, state: 'walking' };
    }
    if (zone === 'entrance') {
      return { x: POIS.entrance.x, y: POIS.entrance.y, state: 'leaving' };
    }
    if (zone === 'away') {
      return { x: POIS.entrance.x, y: POIS.entrance.y + 8, state: 'away' };
    }
    return { x: agent.desk.x, y: agent.desk.y, state: 'idle' };
  }

  function resolveOfficeZone(member) {
    if (member.status === 'working') return 'desk';
    switch (member.office_activity) {
      case 'coffee':
        return 'coffee_room';
      case 'phone':
        return 'phone_room';
      case 'gaming':
        return 'chill_room';
      case 'query':
        return 'desk';
      default:
        break;
    }
    const z = member.office_zone || 'desk';
    if (z === 'coffee') return 'coffee_room';
    if (['coffee_room', 'phone_room', 'chill_room', 'lounge', 'hallway'].includes(z)) {
      return 'desk';
    }
    return z;
  }

  function feedForZone(zone, member) {
    if (member.office_activity === 'coffee' || zone === 'coffee' || zone === 'coffee_room') {
      const b = coffeeBubble(member);
      return { type: 'coffee', message: b.detail };
    }
    if (member.office_activity === 'phone' || zone === 'phone_room') {
      return {
        type: 'talk',
        message: member.current_task || 'On a call',
        extra: member.conversation_partner || 'Call room',
      };
    }
    if (member.office_activity === 'gaming' || zone === 'chill_room') {
      return {
        type: 'walk',
        message: member.current_task || 'Playing games',
        extra: 'Chill & games room',
      };
    }
    if (member.office_activity === 'query' || zone === 'lounge' || zone === 'desk') {
      if (member.office_query) {
        return {
          type: 'talk',
          message: member.office_query,
          extra: member.conversation_partner
            ? `Asking ${member.conversation_partner}`
            : 'Team Q&A at their desk',
        };
      }
      return {
        type: 'talk',
        message: member.current_task || 'Chatting with a teammate',
        extra: member.conversation_partner || member.project_title || 'work',
      };
    }
    if (zone === 'hallway') {
      const b = walkBubble(member);
      return { type: 'walk', message: b.detail };
    }
    if (zone === 'desk' && member.status === 'working') {
      const wb = workBubble(member);
      return {
        type: 'work',
        message: wb.title.replace(/^🟢 |^⚪ /, ''),
        extra: wb.detail,
      };
    }
    return null;
  }

  function applyOfficeZone(agent, member, present) {
    if (!present) {
      if (agent.state !== 'away' && agent.state !== 'leaving') {
        moveAgent(agent, POIS.entrance.x, POIS.entrance.y, 'leaving');
        if (agent.checkedInToday) {
          addFeedEntry('logout', agent.id, `Leaving for the day — last task: ${member.current_task}`);
        }
        setTimeout(() => {
          moveAgent(agent, POIS.entrance.x, POIS.entrance.y + 10, 'away');
          agent.el?.classList.add('fading-out');
        }, 1800);
      }
      return;
    }

    agent.el?.classList.remove('fading-out');

    if ((agent.state === 'away' || agent.state === 'leaving') && !agent.checkedInToday) {
      addFeedEntry('login', agent.id, `Started shift — ${member.current_task}`);
      agent.checkedInToday = true;
    }

    const zone = resolveOfficeZone(member);
    const pos = zonePosition(zone, agent, member);
    const zoneChanged = agent.lastOfficeZone != null && agent.lastOfficeZone !== zone;
    agent.lastOfficeZone = zone;
    moveAgent(agent, pos.x, pos.y, pos.state, member);

    if (zoneChanged) {
      const feed = feedForZone(zone, member);
      if (feed) addFeedEntry(feed.type, agent.id, feed.message, feed.extra || '');
    }
  }

  function tickAgent(agent, index, total, presentAgents) {
    const member = memberByName(agent.id);
    if (!member) return;

    ensureShiftStarted(agent);
    const present = shouldBePresent(agent.id);

    if (minsNow() >= agent.leaveMin && !agent.shiftEnded) {
      agent.shiftEnded = true;
    }

    applyOfficeZone(agent, member, present);
  }

  function renderFloor() {
    if (!container) return;

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
              <span id="office-time-of-day" class="office-time-of-day">🌙 Night</span>
              <span id="office-timezone" class="office-timezone"></span>
              <span class="office-hours">${OFFICE_HOURS_LABEL}</span>
              <span id="office-clock" class="office-clock">--:--</span>
            </div>
          </div>
          <div class="office-floor office-floor-full ${USE_3D_OFFICE ? 'office-floor-3d-mode' : 'office-floor-iso-mode'}">
            ${USE_3D_OFFICE ? '<div id="office-3d-wrap" class="office-3d-wrap"></div>' : buildIsometricFloorHtml()}
            ${officeMemberCardHtml()}
            <div class="${USE_3D_OFFICE ? 'office-3d-legend' : 'office-iso-legend'}">
              <span>💻 Dev Floor</span>
              <span>☕ Coffee Break Room</span>
              <span>📞 Call Booths</span>
              <span>🎮 Gaming Room</span>
              <span>🤝 Meeting Room</span>
            </div>
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
    rosterEl?.addEventListener('click', (e) => {
      const card = e.target.closest('[data-agent]');
      if (!card) return;
      focusMember(card.dataset.agent);
    });
    rosterEl?.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const card = e.target.closest('[data-agent]');
      if (!card) return;
      e.preventDefault();
      focusMember(card.dataset.agent);
    });
    const wrap3d = USE_3D_OFFICE ? document.getElementById('office-3d-wrap') : null;
    scene3dReady = initScene3D(wrap3d);
    agentsEl = document.getElementById('office-agents');
    applyLocalTimeTheme();
    document.getElementById('office-iso-floor')?.addEventListener('click', (e) => {
      const agentEl = e.target.closest('.office-agent');
      if (agentEl?.dataset?.agentId) {
        focusMember(agentEl.dataset.agentId);
      }
    });
  }

  function ensureAgent(member, index) {
    const id = member.name;
    let agent = agents.get(id);
    const deskIdx = deskIndexFor(id);
    const desk = deskForMember(id);

    if (!agent) {
      let el = null;
      if (!scene3d) {
        el = document.createElement('div');
        el.className = 'office-agent state-away';
        el.dataset.agentId = id;
        el.innerHTML = `
          <div class="agent-shadow"></div>
          <div class="agent-body">
            <img class="agent-face" src="${faceUrl(member.name)}" alt="${escapeHtml(member.name)}" />
            <span class="agent-presence-dot offline"></span>
          </div>
          <div class="agent-label-stack">
            <div class="agent-name-tag">${escapeHtml(firstName(member.name))}</div>
            <div class="agent-activity-tag">Standing by</div>
          </div>
        `;
        el.addEventListener('click', (e) => {
          e.stopPropagation();
          focusMember(id);
        });
        if (agentsEl) agentsEl.appendChild(el);
      }
      agent = {
        id, el, desk, deskIndex: deskIdx,
        x: POIS.entrance.x, y: POIS.entrance.y,
        state: 'away', apiWorking: false, lastOfficeZone: null,
        entryMin: assignEntryMin(id),
        leaveMin: assignLeaveMin(id),
        shiftStart: null,
        shiftEnded: false,
        labelOffset: index % 5,
      };
      if (scene3d) {
        scene3d.upsertCharacter(id, member);
      }
      agents.set(id, agent);
    }

    agent.desk = deskForMember(id);
    agent.deskIndex = deskIdx;
    agent.apiWorking = member.status === 'working';
    if (agent.el) {
      agent.el.title = `${member.name}\n${member.current_task}\n${member.work_details || ''}`;
    }
    updateAgentPresence(agent, member);
    const present = shouldBePresent(id);
    applyOfficeZone(agent, member, present);
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
    applyLocalTimeTheme();
    renderRoster();
  }

  async function sync(membersData) {
    if (!container) return;
    members = membersData || [];
    if (!clockEl) renderFloor();
    if (scene3dReady) await scene3dReady;
    if (scene3d) {
      document.getElementById('office-iso-floor')?.classList.add('hidden-behind-3d');
      agents.forEach((agent) => {
        if (agent.el) {
          agent.el.remove();
          agent.el = null;
        }
      });
    } else {
      document.getElementById('office-iso-floor')?.classList.remove('hidden-behind-3d');
    }
    members.forEach((m, i) => ensureAgent(m, i));
    agents.forEach((agent, name) => {
      if (!members.find(m => m.name === name)) {
        agent.el?.remove();
        scene3d?.removeCharacter(name);
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
    tickTimer = setInterval(tick, 1000);
    if (scene3dReady) scene3dReady.then(() => tick());
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
        a.entryMin = assignEntryMin(a.id);
        a.leaveMin = assignLeaveMin(a.id);
      });
    }
  }

  function stop() {
    running = false;
    if (tickTimer) {
      clearInterval(tickTimer);
      tickTimer = null;
    }
    if (scene3d) {
      scene3d.dispose();
      scene3d = null;
    }
  }

  return { start, stop, sync, officePhase, focusMember };
})();
