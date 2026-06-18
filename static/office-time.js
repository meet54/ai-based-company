/** Local timezone time-of-day themes for the virtual office. */

export function getLocalTimePeriod(date = new Date()) {
  const hour = date.getHours();
  if (hour >= 21 || hour < 6) return 'night';
  if (hour < 12) return 'morning';
  if (hour < 17) return 'noon';
  return 'evening';
}

export function getLocalTimezoneLabel() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Local time';
  } catch {
    return 'Local time';
  }
}

const THEMES = {
  night: {
    background: 0x1e2d48,
    fog: 0x243552,
    fogNear: 30,
    fogFar: 62,
    ambient: { color: 0x9aaccc, intensity: 0.62 },
    sun: { color: 0xaabbdd, intensity: 0.38, x: -6, y: 20, z: 10 },
    fill: { color: 0xffd080, intensity: 0.78, x: 12, y: 8, z: 9 },
    hemisphere: { sky: 0x3a4a72, ground: 0x2a3244, intensity: 0.5 },
    interiorBoost: 1.15,
    ceilingLightMult: 1.45,
    exposure: 1.28,
    cssClass: 'office-time-night',
    label: '🌙 Night',
  },
  morning: {
    background: 0xb8ddf0,
    fog: 0xc8e8f6,
    fogNear: 36,
    fogFar: 78,
    ambient: { color: 0xfff8ee, intensity: 0.68 },
    sun: { color: 0xffe0a0, intensity: 0.92, x: 20, y: 15, z: 3 },
    fill: { color: 0xb8ddff, intensity: 0.35, x: 12, y: 8, z: 9 },
    hemisphere: { sky: 0x9fd4f5, ground: 0xa89880, intensity: 0.58 },
    interiorBoost: 0.88,
    ceilingLightMult: 0.82,
    exposure: 1.18,
    cssClass: 'office-time-morning',
    label: '🌅 Morning',
  },
  noon: {
    background: 0x8ec8ea,
    fog: 0x9ed4f0,
    fogNear: 42,
    fogFar: 84,
    ambient: { color: 0xffffff, intensity: 0.72 },
    sun: { color: 0xfffff8, intensity: 1.12, x: 10, y: 30, z: 6 },
    fill: { color: 0xd0ecff, intensity: 0.22, x: 12, y: 8, z: 9 },
    hemisphere: { sky: 0x7ec0e8, ground: 0xb0a890, intensity: 0.52 },
    interiorBoost: 0.75,
    ceilingLightMult: 0.68,
    exposure: 1.15,
    cssClass: 'office-time-noon',
    label: '☀️ Afternoon',
  },
  evening: {
    background: 0x6a5878,
    fog: 0x7a6888,
    fogNear: 32,
    fogFar: 68,
    ambient: { color: 0xffccaa, intensity: 0.58 },
    sun: { color: 0xff8844, intensity: 0.68, x: -16, y: 11, z: 14 },
    fill: { color: 0xffaa66, intensity: 0.55, x: 12, y: 7, z: 9 },
    hemisphere: { sky: 0xff9966, ground: 0x4a3d58, intensity: 0.48 },
    interiorBoost: 1.0,
    ceilingLightMult: 1.15,
    exposure: 1.22,
    cssClass: 'office-time-evening',
    label: '🌆 Evening',
  },
};

export function getTimeOfDayTheme(period) {
  return THEMES[period] || THEMES.noon;
}

export function applyTimePeriodClasses(root, period) {
  if (!root) return;
  Object.keys(THEMES).forEach((p) => root.classList.remove(`office-time-${p}`));
  root.classList.add(`office-time-${period}`);
  root.setAttribute('data-time-period', period);
}
