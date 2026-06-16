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
    background: 0x060b14,
    fog: 0x0a1220,
    fogNear: 20,
    fogFar: 48,
    ambient: { color: 0x3d4f6a, intensity: 0.3 },
    sun: { color: 0x7799cc, intensity: 0.14, x: -6, y: 20, z: 10 },
    fill: { color: 0xffb347, intensity: 0.62, x: 12, y: 5.5, z: 9 },
    hemisphere: { sky: 0x1a2848, ground: 0x080c12, intensity: 0.32 },
    interiorBoost: 1.55,
    cssClass: 'office-time-night',
    label: '🌙 Night',
  },
  morning: {
    background: 0x9fd0ef,
    fog: 0xb8dff2,
    fogNear: 32,
    fogFar: 72,
    ambient: { color: 0xfff4e6, intensity: 0.54 },
    sun: { color: 0xffd080, intensity: 0.78, x: 20, y: 15, z: 3 },
    fill: { color: 0x99ccff, intensity: 0.2, x: 5, y: 7, z: 12 },
    hemisphere: { sky: 0x87ceeb, ground: 0x8b7d6b, intensity: 0.48 },
    interiorBoost: 0.82,
    cssClass: 'office-time-morning',
    label: '🌅 Morning',
  },
  noon: {
    background: 0x6eb8e5,
    fog: 0x82c8ed,
    fogNear: 38,
    fogFar: 78,
    ambient: { color: 0xffffff, intensity: 0.6 },
    sun: { color: 0xfffff2, intensity: 0.98, x: 10, y: 30, z: 6 },
    fill: { color: 0xb8e4ff, intensity: 0.12, x: 5, y: 8, z: 14 },
    hemisphere: { sky: 0x5eb0e5, ground: 0x9a9078, intensity: 0.42 },
    interiorBoost: 0.68,
    cssClass: 'office-time-noon',
    label: '☀️ Afternoon',
  },
  evening: {
    background: 0x4a3d5c,
    fog: 0x6e5a78,
    fogNear: 26,
    fogFar: 58,
    ambient: { color: 0xffaa77, intensity: 0.4 },
    sun: { color: 0xff6633, intensity: 0.52, x: -16, y: 11, z: 14 },
    fill: { color: 0xff8844, intensity: 0.42, x: 12, y: 5.5, z: 9 },
    hemisphere: { sky: 0xff7744, ground: 0x2a2238, intensity: 0.4 },
    interiorBoost: 1.15,
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
