const STORE_KEY = 'bloondesk-save-v1';
const towers = [...new Set(window.BLOONS_TOWERS)];
const mapCatalog = window.BLOONS_MAP_CATEGORIES;
const mapChoices = Object.entries(mapCatalog).flatMap(([category, names]) => names.map(name => ({ name, category })));
const achievementCategories = ['Maps & modes', 'Towers & heroes', 'Co-op', 'Events & challenges', 'Progression', 'Hidden'];
const hiddenAchievementNames = new Set(['Not Lacking Critical Information', 'Alchermistman and Bloonacleboy', 'Golden Ticket', 'Big Bloons', 'Mo Heroes, Mo Problems', 'Strangely Adorable', 'Perfect Paragon', 'Stubborn Strategy', 'Chunky Monkeys', "Josh's Constant", 'They call me Cave Monkey!', "Nah, I'd Win"]);
const achievementStatuses = ['All status', 'To do', 'In progress', 'Completed'];
const appOpenedAt = Date.now();
// Detected values are separate from editable queue/preferences and legacy backups.
// Read-only snapshots come from the local connector, never from imported saves.
let detectedProgress = { maps: {}, towers: {}, achievements: {}, player: null };
let routeUpgradeMemory = { runs: {} };
let towerUpgradeCatalog = {};
let latestGameState = null;
let latestRunLog = '';
let latestAutomationStatus = null;
let automationStatusLoading = false;
let profileRateSamples = [];
let profileRates = { monkeyMoneyPerHour: null, xpPerHour: null };
let profileRateSource = null;
function observeProfileRates(profile) {
  const at = Date.parse(profile?.readAt || '');
  if (!Number.isFinite(at)) return;
  // Keep this identity only in memory. Switching saves (or correcting a guest
  // clock) must not compare balances from unrelated sampling windows.
  const source = JSON.stringify([profile.source || '', profile.file || '']);
  if (source !== profileRateSource || at < (profileRateSamples.at(-1)?.at ?? at)) {
    profileRateSamples = [];
    profileRates = { monkeyMoneyPerHour: null, xpPerHour: null };
    profileRateSource = source;
  }
  if (profileRateSamples.at(-1)?.at === at) return;
  profileRates = { monkeyMoneyPerHour: null, xpPerHour: null };
  const current = { at, monkeyMoney: profile.monkeyMoney, xp: profile.xp,
    rank: profile.rank, veteranXp: profile.veteranXp, veteranRank: profile.veteranRank };
  profileRateSamples.push(current);
  profileRateSamples = profileRateSamples.filter(sample => at - sample.at <= 15 * 60_000).slice(-100);
  const oldest = profileRateSamples.find(sample => at - sample.at >= 30_000);
  if (!oldest) return;
  const hours = (at - oldest.at) / 3_600_000;
  // This is a net balance rate: spending must remain visible, not become zero.
  if (Number.isFinite(current.monkeyMoney) && current.monkeyMoney >= 0
      && Number.isFinite(oldest.monkeyMoney) && oldest.monkeyMoney >= 0)
    profileRates.monkeyMoneyPerHour = (current.monkeyMoney - oldest.monkeyMoney) / hours;
  const xpField = Number.isFinite(current.veteranXp) && Number.isFinite(current.veteranRank) && current.veteranRank > 0
    ? 'veteranXp' : 'xp';
  // Ordinary save XP is cumulative: a rank-up must not reset the rate window.
  // Veteran rollover semantics remain isolated until confirmed from live save evidence.
  const xpBaseline = profileRateSamples.find(sample => at - sample.at >= 30_000
    && (xpField === 'xp' ? sample.rank < 155 && current.rank < 155
      : sample.rank === current.rank && sample.veteranRank === current.veteranRank));
  if (xpBaseline && Number.isFinite(current[xpField]) && Number.isFinite(xpBaseline[xpField])
    && current[xpField] >= xpBaseline[xpField])
    profileRates.xpPerHour = (current[xpField] - xpBaseline[xpField]) / ((at - xpBaseline.at) / 3_600_000);
  else profileRates.xpPerHour = null;
}
let activeBossEvent = null;
let lastRunRefreshAt = 0;
let accumulatedRunLog = { startedAt: null, lines: [] };
let sourceClock = null;
function observeSourceClock(status, requestedAt, receivedAt) {
  // A host relay must retain the guest's clock, never substitute its own.
  // Cached responses cannot calibrate an advancing clock.
  if (status.statusStale || status.statusUnavailable || !Number.isFinite(status.sourceNow)) return;
  sourceClock = { offset: status.sourceNow - (requestedAt + receivedAt) / 2 };
}
function sourceAgeMs(at, now = Date.now()) {
  if (!sourceClock) return null;
  const numeric = typeof at === 'number' || (typeof at === 'string' && /^\d+(?:\.\d+)?$/.test(at));
  const value = numeric ? Number(at) : null;
  const parsed = numeric ? (value < 1e12 ? value * 1000 : value) : Date.parse(at);
  if (!Number.isFinite(parsed)) return null;
  const age = now + sourceClock.offset - parsed;
  // Small request timing differences are normal; large future dates are unknown.
  return age >= -2500 ? Math.max(0, age) : null;
}
try { accumulatedRunLog = { ...accumulatedRunLog, ...JSON.parse(localStorage.getItem('bloonsRunLog') || '{}') }; } catch { /* storage unavailable */ }
function keepRunLog(status) {
  const incoming = Array.isArray(status.log) ? status.log : [];
  if (status.running && status.startedAt && accumulatedRunLog.startedAt !== status.startedAt) {
    accumulatedRunLog = { startedAt: status.startedAt, lines: [] };
  }
  const saved = accumulatedRunLog.lines || [];
  let overlap = 0;
  for (let count = Math.min(saved.length, incoming.length); count > 0; count--) {
    if (saved.slice(-count).every((line, index) => line === incoming[index])) { overlap = count; break; }
  }
  accumulatedRunLog.lines = [...saved, ...incoming.slice(overlap)].slice(-2000);
  try { localStorage.setItem('bloonsRunLog', JSON.stringify(accumulatedRunLog)); } catch { /* storage full */ }
  return accumulatedRunLog.lines;
}
const defaults = { queue: [], completedMaps: [], achievements: [], completed: [], towerChecks: {}, achievementProgress: {}, theme: 'light', startupMode:'full' };
let state = loadState();
document.documentElement.dataset.theme = state.theme === 'dark' ? 'dark' : 'light';
let toastTimer;
let activeAchievementCategory = 'All';
let activeAchievementStatus = 'All status';
let achievementQuery = '';

function loadState() {
  try {
    const restored = { ...defaults, ...JSON.parse(localStorage.getItem(STORE_KEY) || '{}') };
    restored.completedMaps = [...new Set([...(restored.completedMaps || []), ...(restored.queue || []).filter(item => item.done).map(item => item.name)])];
    return restored;
  }
  catch { return { ...defaults }; }
}
function saveState() { localStorage.setItem(STORE_KEY, JSON.stringify(state)); render(); }
function notify(message) {
  const toast = document.querySelector('#toast'); toast.textContent = message; toast.classList.add('show');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
}
function showView(view) {
  if (view === 'specific-map' || view === 'towers') view = 'automation';
  document.body.classList.toggle('boss-view-active', view === 'bosses');
  document.querySelectorAll('.view').forEach(el => el.classList.toggle('hidden', el.id !== view));
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === view);
    if (el.dataset.view === view) el.setAttribute('aria-current', 'page'); else el.removeAttribute('aria-current');
  });
  document.querySelector('#page-title').textContent = ({ overview: 'Overview', blackborder: 'Maps', achievements: 'Achievements', towers: 'Tower progress', automation: 'Automation', bosses: 'Boss events', logs: 'Run logs', 'specific-map': 'Specific map', settings: 'Settings' })[view] || 'Overview';
  if (view === 'blackborder') renderMaps();
  if (view === 'achievements') renderAchievements();
  if (view === 'automation' || view === 'overview') loadAutomationStatus();
  window.scrollTo(0, 0);
  document.querySelector('main')?.scrollTo?.(0, 0);
  try { localStorage.setItem('bloonsplus-last-view', view); } catch { /* private/blocked storage: page just won't be remembered */ }
  if (view === 'blackborder' || view === 'automation') {
    loadDetectedProgress();
    refreshLocalSaveProgress();
  }
  if (view === 'towers') refreshLocalSaveProgress();
  if (view === 'bosses') renderBossHub();
  if (view === 'logs') loadRouteFailures();
  if (view === 'settings') document.dispatchEvent(new Event('bloons-settings-open'));
}
async function refreshBossEvent() {
  if (!document.querySelector('#boss-event-requirements')) return;
  try {
    const response = await fetch('/api/boss-event', { cache: 'no-store', signal: AbortSignal.timeout(12000) });
    const body = await response.text();
    let parsed = null;
    try { parsed = JSON.parse(body); } catch { parsed = { available: false, active: false, reason: body.slice(0, 180) || `HTTP ${response.status}` }; }
    activeBossEvent = response.ok ? parsed : { available: false, active: false, reason: parsed.reason || `Boss event request failed (${response.status})` };
  } catch (error) {
    activeBossEvent = { available: false, reason: error.message };
  }
  renderBossHub();
}
// Generated boss routes, keyed by "${bossId}:${variant}". renderBossHub() rebuilds every
// button from scratch on each view switch and its own 3-minute event poll, so a route
// path kept only on the button's DOM dataset was silently lost on the very next render —
// this survives both, and a page reload too.
let bossRouteStore = {};
try { bossRouteStore = JSON.parse(localStorage.getItem('bloonsplus-boss-routes') || '{}'); } catch { bossRouteStore = {}; }
function saveBossRoute(bossId, variant, routePath) {
  bossRouteStore[`${bossId}:${variant}`] = routePath;
  try { localStorage.setItem('bloonsplus-boss-routes', JSON.stringify(bossRouteStore)); } catch { /* private/blocked storage: route just won't survive a reload */ }
}
function renderBossHub() {
  if (document.querySelector('#bosses')?.classList.contains('hidden')) return;
  const list = document.querySelector('#boss-list');
  if (!list || !Array.isArray(window.BLOONS_BOSSES)) return;
  const profile = detectedProgress.localProfile;
  const badgeEvents = Object.values(profile?.bossMedals || {});
  const normalBadges = badgeEvents.reduce((sum, entry) => sum + (Number(entry?.normalBadges) || 0), 0);
  const eliteBadges = badgeEvents.reduce((sum, entry) => sum + (Number(entry?.eliteBadges) || 0), 0);
  const medalCount = document.querySelector('#boss-medal-count');
  if (medalCount) medalCount.textContent = badgeEvents.length ? `${normalBadges} Normal · ${eliteBadges} Elite` : 'Not stored per boss';
  const activeName = document.querySelector('#boss-active-name');
  const activeDetail = document.querySelector('#boss-active-detail');
  const requirements = document.querySelector('#boss-event-requirements');
  if (activeName && activeDetail && requirements) {
    if (!activeBossEvent) {
      activeName.textContent = 'Checking…';
      activeDetail.textContent = 'Reading Ninja Kiwi’s public event list.';
      requirements.textContent = 'Checking the current event…';
    } else if (!activeBossEvent.available) {
      activeName.textContent = 'Event data unavailable';
      activeDetail.textContent = activeBossEvent.reason || 'The public event API could not be reached.';
      requirements.textContent = 'The current map and restrictions are unknown. Boss automation remains unavailable.';
    } else if (!activeBossEvent.active) {
      activeName.textContent = 'No active event';
      activeDetail.textContent = 'Ninja Kiwi lists no active boss right now.';
      requirements.textContent = 'Normal and Elite requirements will appear when a boss event starts.';
    } else {
      const label = window.BLOONS_BOSSES.find(item => item.id === activeBossEvent.bossType)?.name || activeBossEvent.bossType;
      const map = activeBossEvent.metadata?.normal?.map || activeBossEvent.metadata?.elite?.map || 'Unknown map';
      activeName.textContent = `${label} · ${map}`;
      activeDetail.textContent = `Official event · ends ${new Date(activeBossEvent.end).toLocaleString()}`;
      const panels = ['normal', 'elite'].map(variant => {
        const meta = activeBossEvent.metadata?.[variant];
        const card = document.createElement('article'); card.className = 'boss-event-variant';
        const heading = document.createElement('h4'); heading.textContent = variant === 'normal' ? 'Normal' : 'Elite';
        card.append(heading);
        if (!meta) { card.append(document.createTextNode('Event rules unavailable.')); return card; }
        const facts = [
          `Map: ${meta.map} · ${meta.difficulty} ${meta.mode}`,
          `Rounds ${meta.startRound}–${meta.endRound} · starting cash ${Number.isFinite(meta.startingCash) ? meta.startingCash.toLocaleString() : 'unknown'}`,
          `Boss health ×${meta.bossHealth} · speed ×${meta.bossSpeed}`,
          `Max towers ${meta.maxTowers < 0 || meta.maxTowers >= 9999 ? 'no practical limit' : meta.maxTowers} · max Paragons ${meta.maxParagons < 0 ? 'unlimited' : meta.maxParagons}`,
          `Monkey Knowledge ${meta.disableMK ? 'off' : 'allowed'} · selling ${meta.disableSelling ? 'off' : 'allowed'}`,
        ];
        const limited = meta.limitedTowers || [];
        const bannedTowers = limited.filter(tower => !tower.isHero && tower.max === 0);
        const allowedHeroes = limited.filter(tower => tower.isHero && tower.max > 0);
        if (bannedTowers.length) facts.push(`Banned towers: ${bannedTowers.map(tower => tower.tower).join(', ')}`);
        if (allowedHeroes.length) facts.push(`Allowed heroes: ${allowedHeroes.map(hero => hero.tower).join(', ')}`);
        const list = document.createElement('ul');
        for (const fact of facts) { const item = document.createElement('li'); item.textContent = fact; list.append(item); }
        card.append(list); return card;
      });
      requirements.replaceChildren(...panels);
    }
  }
  let readyRoutes = 0;
  list.replaceChildren(...window.BLOONS_BOSSES.map(boss => {
    const card = document.createElement('article'); card.className = 'boss-card';
    const head = document.createElement('div'); head.className = 'boss-card-head';
    const mark = document.createElement('span'); mark.className = `boss-mark boss-${boss.id}`; mark.textContent = boss.name.slice(0, 1);
    const title = document.createElement('div');
    const name = document.createElement('b'); name.textContent = boss.name;
    const subtitle = document.createElement('small'); subtitle.textContent = boss.subtitle;
    title.append(name, subtitle); head.append(mark, title);
    const mechanic = document.createElement('p'); mechanic.className = 'boss-mechanic'; mechanic.textContent = boss.mechanic;
    const variants = document.createElement('div'); variants.className = 'boss-variants';
    for (const difficulty of ['Normal', 'Elite']) {
      const row = document.createElement('div'); row.className = 'boss-variant-row';
      const label = document.createElement('b'); label.textContent = difficulty;
      const route = boss.routes?.[difficulty.toLowerCase()];
      const status = document.createElement('span'); status.className = `boss-route-pending${route?.verified ? ' boss-route-ready' : ''}`;
      status.textContent = route?.verified ? `Verified route · ${route.name || 'ready'}` : 'Research draft · no executable route';
      if (route?.verified) readyRoutes++;
      const generate = document.createElement('button'); generate.className = 'quiet-button boss-run-button';
      const storedRoute = bossRouteStore[`${boss.id}:${difficulty.toLowerCase()}`];
      if (storedRoute) { generate.dataset.route = storedRoute; generate.textContent = 'Run route'; status.textContent = `Generated route · experimental · ${storedRoute.split('/').pop()}`; }
      else generate.textContent = 'Generate route';
      generate.addEventListener('click', async () => {
        if (generate.dataset.route) return startFarmJob({ type: 'file', file: generate.dataset.route, gamemode: difficulty.toLowerCase() });
        generate.disabled = true; generate.textContent = 'Preparing…';
        try {
          const response = await fetch('/api/boss-route/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ elite: difficulty === 'Elite' }) });
          const raw = await response.text();
          let result; try { result = JSON.parse(raw); } catch { result = { error: raw.slice(0, 180) || `HTTP ${response.status}` }; }
          if (!response.ok || !result.available) throw new Error(result.reason || result.error || 'No route could be generated');
          status.textContent = `Generated route · ${result.map} · experimental`;
          generate.textContent = 'Run route';
          const routePath = result.route.replace(/\\/g, '/');
          generate.dataset.route = routePath;
          saveBossRoute(boss.id, difficulty.toLowerCase(), routePath);
          generate.disabled = false;
        } catch (error) { status.textContent = error.message; generate.textContent = 'Retry'; generate.disabled = false; }
      });
      row.append(label, status, generate); variants.append(row);
    }
    const plans = window.BLOONS_BOSS_PLANS?.[boss.id];
    card.append(head, mechanic, variants);
    if (plans) {
      const details = document.createElement('details'); details.className = 'boss-plan';
      const summary = document.createElement('summary'); summary.textContent = 'View Normal and Elite research plans';
      details.append(summary);
      for (const variant of ['normal', 'elite']) {
        const heading = document.createElement('h4'); heading.textContent = variant === 'normal' ? 'Normal' : 'Elite';
        const steps = document.createElement('ol');
        for (const step of plans[variant] || []) { const item = document.createElement('li'); item.textContent = step; steps.append(item); }
        details.append(heading, steps);
      }
      const source = document.createElement('a'); source.href = plans.source; source.target = '_blank'; source.rel = 'noopener noreferrer'; source.textContent = 'Research source ↗';
      details.append(source); card.append(details);
    }
    return card;
  }));
  const routeCount = document.querySelector('#boss-route-count');
  if (routeCount) routeCount.textContent = `${readyRoutes} / ${window.BLOONS_BOSSES.length * 2}`;
}
setInterval(() => {
  if (!document.hidden && !document.querySelector('#bosses')?.classList.contains('hidden')) refreshBossEvent();
}, 180000);
// Medal slots in the game's own order, with the difficulty tier that colours each medal.
const MEDAL_SLOTS = [
  ['easy', 'easy', 'E', 'Easy'], ['primary_only', 'easy', 'P', 'Primary Only'], ['deflation', 'easy', 'D', 'Deflation'],
  ['medium', 'medium', 'M', 'Medium'], ['military_only', 'medium', 'Mi', 'Military Only'], ['reverse', 'medium', 'R', 'Reverse'], ['apopalypse', 'medium', 'A', 'Apopalypse'],
  ['hard', 'hard', 'H', 'Hard'], ['magic_monkeys_only', 'hard', 'Mg', 'Magic Monkeys Only'], ['double_hp_moabs', 'hard', '2x', 'Double HP MOABs'], ['half_cash', 'hard', '½', 'Half Cash'],
  ['alternate_bloons_rounds', 'hard', 'AB', 'Alternate Bloons Rounds'], ['impoppable', 'impoppable', 'I', 'Impoppable'], ['chimps', 'chimps', 'C', 'CHIMPS'],
];
const MEDAL_BY_MODE = Object.fromEntries(MEDAL_SLOTS.map(slot => [slot[0], slot]));
let mapsCategory = 'All';
const iconSlug = name => name.toLowerCase().replace(/[^a-z0-9]/g, '');
// Custom medal: hexagon badge with its own colour per mode, a star for the standard modes, an icon
// for each variation, and a skull for Impoppable and CHIMPS. Not earned: light gray.
function medalIcon(mode, earned) {
  const [, tier, , label] = MEDAL_BY_MODE[mode] || [mode, 'hard', '?', mode];
  const standard = ['easy', 'medium', 'hard'].includes(mode);
  const skull = mode === 'impoppable' || mode === 'chimps';
  const medal = document.createElement('span');
  medal.className = `medal medal-${tier} mode-${mode} ${earned === true ? 'earned' : earned === false ? 'missing' : 'unknown'}`;
  medal.title = `${label}: ${earned === true ? 'earned' : earned === false ? 'not earned yet' : 'not scanned'}`;
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 24 28'); svg.setAttribute('aria-hidden', 'true');
  const shape = document.createElementNS(ns, 'use'); shape.setAttribute('href', '#medal-shape'); svg.append(shape);
  const mark = document.createElementNS(ns, 'use');
  mark.setAttribute('href', skull ? '#medal-skull' : standard ? '#medal-star' : `#medal-${mode}`);
  svg.append(mark);
  medal.append(svg);
  return medal;
}
// The map's own tile art once the scanner has seen it on the map-select screen, initials until then.
function mapThumb(name, category) {
  const thumb = document.createElement('span'); thumb.className = `map-thumb cat-${(category || 'custom').toLowerCase()}`;
  thumb.textContent = name.split(/\s+/).map(word => word[0]).join('').slice(0, 2).toUpperCase();
  const img = document.createElement('img'); img.alt = ''; img.src = `map-icons/${iconSlug(name)}.png`;
  img.addEventListener('load', () => thumb.classList.add('has-image'));
  img.addEventListener('error', () => img.remove());
  thumb.append(img);
  return thumb;
}
const mapProgressKey = BloonsMapNames.normalize;
const mapObservationFor = name => {
  const entries = Object.entries(detectedProgress.maps || {}).filter(([key]) => mapProgressKey(key) === mapProgressKey(name));
  const saved = entry => entry.localSaveSource === 'btd6-profile-save';
  const observedAt = entry => {
    const value = Date.parse(saved(entry) ? entry.localSaveReadAt : entry.updatedAt || entry.scannedAt);
    return Number.isFinite(value) ? value : 0;
  };
  // Save records include explicit false medals. Never let an OCR alias overwrite
  // them, even when the scan is newer or either timestamp is unavailable.
  entries.sort((a,b) => Number(saved(a[1])) - Number(saved(b[1])) || observedAt(a[1]) - observedAt(b[1]));
  return entries.reduce((result, [,entry]) => ({...result, ...entry, medals: {...result.medals, ...entry.medals}}), {});
};
function medalsFromLocalRecord(record) {
  return BloonsMedals.medalsFromMapRecord(record);
}
let lastMapRenderKey = null;
function renderMaps() {
  if (document.querySelector('#blackborder')?.classList.contains('hidden')) return;
  const grid = document.querySelector('#maps-grid'); if (!grid) return;
  const filters = document.querySelector('#maps-filters');
  if (!filters.childElementCount) {
    ['All', ...Object.keys(mapCatalog)].forEach(category => {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'filter-chip'; button.textContent = category;
      button.addEventListener('click', () => { mapsCategory = category; renderMaps(); });
      filters.append(button);
    });
    const legend = document.querySelector('#medal-legend');
    legend.replaceChildren(...MEDAL_SLOTS.map(([mode, , , label]) => { const item = document.createElement('span'); item.append(medalIcon(mode, true), label); return item; }));
  }
  filters.querySelectorAll('.filter-chip').forEach(button => button.classList.toggle('active', button.textContent === mapsCategory));
  const query = (document.querySelector('#maps-search')?.value || '').trim().toLowerCase();
  const hideDone = document.querySelector('#maps-hide-done')?.checked;
  // A save read changes its timestamp on every poll. Only medal content and
  // filters change these cards; retain their nodes across identical reads.
  const observations = mapChoices.map(map => {
    const observation = mapObservationFor(map.name);
    return { ...map, medals: observation.medals, done: observation.blackBorder === true
      || MEDAL_SLOTS.every(([mode]) => observation.medals?.[mode] === true) };
  });
  const renderKey = JSON.stringify([mapsCategory, query, hideDone, observations.map(map =>
    [map.name, map.category, map.done, Boolean(map.medals), MEDAL_SLOTS.map(([mode]) => map.medals?.[mode] ?? null)])]);
  if (renderKey === lastMapRenderKey) return;
  const cards = observations.filter(map => (mapsCategory === 'All' || map.category === mapsCategory)
    && map.name.toLowerCase().includes(query) && !(hideDone && map.done)).map(map => {
    const medals = map.medals;
    const earned = MEDAL_SLOTS.filter(([mode]) => medals?.[mode] === true).length;
    const card = document.createElement('article'); card.className = `map-card${map.done ? ' done' : ''}`;
    const head = document.createElement('div'); head.className = 'map-card-head';
    const info = document.createElement('div'); info.className = 'map-card-info';
    const name = document.createElement('b'); name.textContent = map.name;
    const meta = document.createElement('small');
    meta.textContent = `${map.category} · ${map.done ? 'Black bordered' : medals ? `${earned}/${MEDAL_SLOTS.length} medals` : 'Not scanned'}`;
    info.append(name, meta); head.append(mapThumb(map.name, map.category), info);
    const row = document.createElement('div'); row.className = 'medal-row';
    // A medal the scan did not report stays "not scanned" rather than counted as missing.
    row.append(...MEDAL_SLOTS.map(([mode]) => medalIcon(mode, medals && mode in medals ? medals[mode] === true : undefined)));
    card.append(head, row);
    return card;
  });
  if (!cards.length) { const empty = document.createElement('p'); empty.className = 'muted'; empty.textContent = 'No maps match.'; cards.push(empty); }
  grid.replaceChildren(...cards);
  document.querySelector('#queue-count').textContent = observations.filter(map => !map.done).length;
  lastMapRenderKey = renderKey;
}
function findMap(name) { return mapChoices.find(map => map.name.toLowerCase() === name.toLowerCase()); }
// Black border = every medal on the map, whether the game's border read or the medal row says so.
function isMapDone(name) {
  const map = mapObservationFor(name);
  return map?.blackBorder === true || MEDAL_SLOTS.every(([mode]) => map?.medals?.[mode] === true);
}
function mapStatus(name) {
  const map = mapObservationFor(name);
  return map?.blackBorder ? 'Black bordered' : map?.status === 'working' ? 'In progress' : map?.status === 'todo' ? 'Uncompleted' : 'Not scanned';
}
const TOWER_NAMES = { dart: 'Dart Monkey', boomerang: 'Boomerang Monkey', bomb: 'Bomb Shooter', tack: 'Tack Shooter', ice: 'Ice Monkey', glue: 'Glue Gunner', desperado: 'Desperado', sniper: 'Sniper Monkey', sub: 'Monkey Sub', buccaneer: 'Monkey Buccaneer', ace: 'Monkey Ace', heli: 'Heli Pilot', mortar: 'Mortar Monkey', dartling: 'Dartling Gunner', wizard: 'Wizard Monkey', super: 'Super Monkey', ninja: 'Ninja Monkey', alchemist: 'Alchemist', druid: 'Druid', farm: 'Banana Farm', spike: 'Spike Factory', village: 'Monkey Village', engineer: 'Engineer Monkey', beasthandler: 'Beast Handler', mermonkey: 'Mermonkey', skywarden: 'Skywarden' };
const TOWER_UPGRADE_SLUGS = { 'Dart Monkey':'dart','Boomerang Monkey':'boomer','Bomb Shooter':'bomb','Tack Shooter':'tack','Ice Monkey':'ice','Glue Gunner':'glue','Desperado':'desperado','Sniper Monkey':'sniper','Monkey Sub':'sub','Monkey Buccaneer':'boat','Monkey Ace':'ace','Heli Pilot':'heli','Mortar Monkey':'mortar','Dartling Gunner':'dartling','Wizard Monkey':'wizard','Super Monkey':'super','Ninja Monkey':'ninja','Alchemist':'alch','Druid':'druid','Banana Farm':'farm','Spike Factory':'spike','Monkey Village':'village','Engineer Monkey':'engineer','Beast Handler':'beast','Mermonkey':'mermonkey','Skywarden':'skywarden' };
const TOWER_RUN_TYPE_ALIASES = { 'Monkey Buccaneer':['buccaneer','boat'], 'Alchemist':['alch','alchemist'], 'Beast Handler':['beasthandler','beast'], 'Boomerang Monkey':['boomer','boomerang'] };
const normalizeUpgradeName = value => String(value).toLowerCase().replace(/[^a-z0-9]/g, '');
function upgradeNameFor(towerName, pathIndex, tier) {
  const slug = TOWER_UPGRADE_SLUGS[towerName];
  if (!slug) return null;
  const suffix = pathIndex === 0 ? `${tier}-x-x` : pathIndex === 1 ? `x-${tier}-x` : `x-x-${tier}`;
  const entry = Object.entries(towerUpgradeCatalog).find(([id]) => id.toLowerCase() === `${slug} ${suffix}`.toLowerCase());
  return typeof entry?.[1]?.[0] === 'string' ? entry[1][0] : null;
}
function unlockedUpgradeSet() { return new Set((detectedProgress.localProfile?.acquiredUpgrades || []).map(normalizeUpgradeName)); }
function ownsUpgrade(owned, towerName, upgradeName) {
  return SaveUpgradeNames.owns(owned, towerName, upgradeName);
}
// Shared by renderTowers() and renderTowerRequirements() so a tower's catalog coverage
// (e.g. Skywarden's tiers, once tower-upgrade-overrides.json supplies them) can't be
// special-cased correctly in one place and forgotten in the other.
function upgradeTierKnown(upgradeName, hasUpgradeData) {
  return hasUpgradeData && !!upgradeName;
}
function towerUnlockStatus(local, towerName) {
  const values = local?.unlockedTowers;
  if (!Array.isArray(values)) return 'unknown';
  const normalizedValues = values.map(value => normalizeUpgradeName(
    typeof value === 'string' ? value : value?.name || value?.towerName || value?.id || value?.type || ''
  ));
  const candidates = new Set([towerName, TOWER_UPGRADE_SLUGS[towerName], ...(TOWER_RUN_TYPE_ALIASES[towerName] || [])]
    .filter(Boolean).map(normalizeUpgradeName));
  return normalizedValues.some(value => candidates.has(value)) ? 'unlocked'
    : normalizedValues.length ? 'unmapped' : 'unknown';
}
// Primary/Military/Magic/Support colour classes, same grouping BTD6's own tower shop tabs use.
const TOWER_CLASS = { 'Dart Monkey': 'primary', 'Boomerang Monkey': 'primary', 'Bomb Shooter': 'primary', 'Tack Shooter': 'primary', 'Ice Monkey': 'primary', 'Glue Gunner': 'primary', 'Desperado': 'primary',
  'Sniper Monkey': 'military', 'Monkey Sub': 'military', 'Monkey Buccaneer': 'military', 'Monkey Ace': 'military', 'Heli Pilot': 'military', 'Mortar Monkey': 'military', 'Dartling Gunner': 'military',
  'Wizard Monkey': 'magic', 'Super Monkey': 'magic', 'Ninja Monkey': 'magic', 'Alchemist': 'magic', 'Druid': 'magic', 'Mermonkey': 'magic', 'Skywarden': 'magic',
  'Banana Farm': 'support', 'Spike Factory': 'support', 'Monkey Village': 'support', 'Engineer Monkey': 'support', 'Beast Handler': 'support' };
// No official art is bundled (BTD6's own assets aren't read from), so this is a generated
// placeholder: the tower's own class colour with its initials, not real tower art.
// Real card art cropped from the Towers screen the first time each tower was scanned there
// (scan-towers.js's tower-icons/), with the class-coloured initials as a fallback until that
// tower has been seen and scanned once.
const towerIconSlug = name => name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
function towerThumb(name) {
  const cls = TOWER_CLASS[name] || 'primary';
  const thumb = document.createElement('span'); thumb.className = `tower-thumb tower-cls-${cls}`;
  thumb.textContent = name.split(/\s+/).map(word => word[0]).join('').slice(0, 2).toUpperCase();
  thumb.title = name;
  const img = document.createElement('img'); img.alt = ''; img.src = `tower-icons/${towerIconSlug(name)}.png`;
  img.addEventListener('load', () => thumb.classList.add('has-image'));
  img.addEventListener('error', () => img.remove());
  thumb.append(img);
  return thumb;
}
function renderTowers() {
  if (document.querySelector('#towers')?.classList.contains('hidden')) return;
  const list = document.querySelector('#tower-list'); list.replaceChildren();
  const local = detectedProgress.localProfile || {};
  const upgradeDataReady = Array.isArray(local.acquiredUpgrades);
  const owned = unlockedUpgradeSet();
  const towerKey = value => String(value).toLowerCase().replace(/[^a-z0-9]/g, '');
  const observationFor = name => detectedProgress.towers[name]
    || Object.entries(detectedProgress.towers || {}).find(([key]) => towerKey(key) === towerKey(name))?.[1];
  towers.forEach(name => {
    const observation = observationFor(name);
    const cls = TOWER_CLASS[name] || 'primary';
    const card = document.createElement('article'); card.className = `tower-card tower-cls-${cls}`;
    const art = document.createElement('div'); art.className = 'tower-card-art'; art.append(towerThumb(name));
    const body = document.createElement('div'); body.className = 'tower-card-body';
    const head = document.createElement('div'); head.className = 'tower-card-head';
    const title = document.createElement('b'); title.textContent = name;
    const chip = document.createElement('span'); chip.className = 'tower-class-chip'; chip.textContent = cls;
    const unlockStatus = towerUnlockStatus(local, name);
    const unlock = document.createElement('span'); unlock.className = `tower-unlock-chip tower-unlock-${unlockStatus}`;
    unlock.textContent = unlockStatus === 'unlocked' ? 'Unlocked' : unlockStatus === 'unmapped' ? 'Unlock ID unmapped' : 'Unlock unknown';
    head.append(title, chip, unlock);
    body.append(head);
    const paths = document.createElement('div'); paths.className = 'tower-path-grid';
    for (let pathIndex = 0; pathIndex < 3; pathIndex++) {
      const pathRow = document.createElement('div'); pathRow.className = 'tower-path-row';
      const label = document.createElement('span'); label.textContent = `P${pathIndex + 1}`; pathRow.append(label);
      for (let tier = 1; tier <= 5; tier++) {
        const upgradeName = upgradeNameFor(name, pathIndex, tier);
        const unlocked = ownsUpgrade(owned, name, upgradeName);
        const known = upgradeTierKnown(upgradeName, upgradeDataReady);
        const tierNode = document.createElement('span'); tierNode.className = `tower-tier ${unlocked ? 'unlocked' : known ? 'locked' : 'unknown'}`;
        tierNode.textContent = `${unlocked ? '✓' : known ? '×' : '?'} T${tier}`;
        tierNode.title = upgradeName ? `${upgradeName}${unlocked ? ' · unlocked' : known ? ' · not unlocked' : ' · tier ID unverified or profile unavailable'}` : `Tier ${tier} · upgrade name unavailable in catalog`;
        pathRow.append(tierNode);
      }
      paths.append(pathRow);
    }
    body.append(paths);
    const knownTierCount = Array.from({ length: 3 }, (_, pathIndex) => Array.from({ length: 5 }, (_, tierIndex) => upgradeNameFor(name, pathIndex, tierIndex + 1)).filter(Boolean).length).reduce((sum, count) => sum + count, 0);
    const unlockedCount = Array.from({ length: 3 }, (_, pathIndex) => Array.from({ length: 5 }, (_, tierIndex) => {
      const upgrade = upgradeNameFor(name, pathIndex, tierIndex + 1);
      return ownsUpgrade(owned, name, upgrade);
    }).filter(Boolean).length).reduce((sum, count) => sum + count, 0);
    const tierSummary = document.createElement('small'); tierSummary.className = 'tower-tier-summary';
    tierSummary.textContent = upgradeDataReady
      ? `${unlockedCount} unlocked · ${Math.max(0, knownTierCount - unlockedCount)} locked${knownTierCount < 15 ? ` · ${15 - knownTierCount} tiers missing from upgrade catalog` : ''}`
      : local.available ? 'VM upgrade list unavailable; update the VM reader' : 'Upgrade unlock data unavailable';
    body.append(tierSummary);
    // The Profile.Save path above shows permanent unlocks. Show live per-run path
    // tiers separately so purchases made in the VM are visible on this PC too.
    const slug = TOWER_UPGRADE_SLUGS[name];
    const normalizeTower = value => String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    const aliases = (TOWER_RUN_TYPE_ALIASES[name] || [slug, name]).map(normalizeTower);
    const runEntries = Object.entries(latestGameState?.towers || {}).filter(([, tower]) => aliases.includes(normalizeTower(tower.type)));
    if (runEntries.length) {
      const runPaths = document.createElement('small'); runPaths.className = 'tower-xp-line tower-run-paths';
      const pathsText = runEntries.map(([instance, tower]) => {
        const levels = Array.isArray(tower.upgrades) ? tower.upgrades : [0, 0, 0];
        const labels = levels.map((level, index) => {
          const tier = Math.max(0, Math.min(5, Number(level) || 0));
          const upgrade = tier ? upgradeNameFor(name, index, tier) : null;
          return `P${index + 1} ${tier}${upgrade ? ` · ${upgrade}` : ''}`;
        });
        return `${instance} ${labels.join(' · ')}`;
      }).join('  |  ');
      const runMap = latestGameState?.map ? ` · ${String(latestGameState.map).replace(/_/g, ' ')}` : '';
      runPaths.textContent = `Last run${runMap}: ${pathsText}`;
      body.append(runPaths);
    }
    if (observation?.complete === true || observation?.complete === false) {
      const status = document.createElement('span'); status.className = 'tower-status-line';
      status.textContent = observation.complete ? '✓ Complete' : 'Upgrades remaining';
      status.classList.toggle('is-complete', observation.complete === true);
      body.append(status);
    }
    if (Number.isFinite(observation?.xp) && observation.xp >= 0) {
      const xp = document.createElement('small'); xp.className = 'tower-xp-line';
      xp.textContent = `${observation.xp.toLocaleString()} XP available`;
      if (observation.selectedUpgrade) {
        const upgrade = observation.selectedUpgrade;
        if (Number.isFinite(upgrade.cost)) xp.textContent = `${observation.xp.toLocaleString()} XP · ${upgrade.name}: ${(upgrade.cost - observation.xp > 0 ? `${(upgrade.cost - observation.xp).toLocaleString()} more needed` : 'ready')}`;
      }
      body.append(xp);
    }
    card.append(art, body);
    list.append(card);
  });
  const history = document.querySelector('#route-upgrade-list');
  if (!history) return;
  history.replaceChildren();
  const entries = Object.values(routeUpgradeMemory.runs || {}).flatMap(run =>
    Object.entries(run.towers || {}).flatMap(([instance, tower]) => {
      const levels = Array.isArray(tower.upgrades) ? tower.upgrades : [0, 0, 0];
      const total = levels.reduce((sum, level) => sum + (Number.isInteger(level) ? level : 0), 0);
      return total ? [{ run, instance, tower, levels, total }] : [];
    })
  ).sort((a, b) => String(b.tower.lastUpdated || b.run.startedAt || '').localeCompare(String(a.tower.lastUpdated || a.run.startedAt || '')));
  if (!entries.length) {
    const empty = document.createElement('p'); empty.className = 'route-upgrade-empty'; empty.textContent = 'No confirmed upgrade purchases recorded yet.'; history.append(empty); return;
  }
  entries.forEach(({ run, instance, tower, levels, total }) => {
    const row = document.createElement('div'); row.className = 'route-upgrade-row';
    const towerLabel = document.createElement('b'); towerLabel.textContent = `${tower.type || 'Tower'} · ${instance}`;
    const details = document.createElement('span');
    details.textContent = `${run.map || 'Map'} · ${run.difficulty || 'Difficulty'} / ${run.gamemode || 'mode'} · paths ${levels.join('/')}`;
    const count = document.createElement('strong'); count.textContent = `${total} confirmed`;
    row.append(towerLabel, details, count);
    history.append(row);
  });
}
function renderGameState() {
  const summary = document.querySelector('#game-state-summary');
  const details = document.querySelector('#game-state-details');
  if (!summary || !details) return;
  if (!latestGameState?.runId) {
    summary.textContent = 'Waiting for a deterministic run snapshot.';
    details.innerHTML = '<span>Map <b>—</b></span><span>Mode <b>—</b></span><span>Round <b>—</b></span><span>Cash <b>—</b></span><span>Result <b>—</b></span><span>Towers <b>—</b></span>';
    return;
  }
  const state = latestGameState;
  const titleCase = value => String(value || '').replace(/[_-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  summary.textContent = `Last observed ${state.updatedAt ? new Date(state.updatedAt).toLocaleString() : 'time unknown'} · ${state.screen || 'screen unknown'}`;
  const values = [
    ['Map', titleCase(state.map) || '—'],
    ['Mode', [state.difficulty, state.mode].filter(Boolean).map(titleCase).join(' · ') || '—'],
    ['Round', Number.isInteger(state.round) ? state.round : '—'],
    ['Cash', Number.isInteger(state.cash) ? state.cash.toLocaleString() : '—'],
    ['Result', titleCase(state.result || 'In progress')],
    ['Towers', Object.keys(state.towers || {}).length],
  ];
  details.replaceChildren(...values.map(([label, value]) => {
    const item = document.createElement('span'); item.append(document.createTextNode(`${label} `));
    const strong = document.createElement('b'); strong.textContent = value; item.append(strong); return item;
  }));
}
function achievementCategory(name) {
  if (hiddenAchievementNames.has(name)) return 'Hidden';
  if (/co-operation|co-op|benefactor|philanthropist|contributor|bill greates|triple threat|four times|collaborate|player one|powershare|social butterfly/i.test(name)) return 'Co-op';
  if (/challenge|daily|race|odyssey|territory|season|boss|quest|crate|limited run|team player|team captain|team-up/i.test(name)) return 'Events & challenges';
  if (/map|medal|chimps|impoppable|survivor|role reverser|bloons master|2tc|megapops|inflated|thrifty|poppable|indie|no harvest|spiiicey/i.test(name)) return 'Maps & modes';
  if (/monkey|hero|tower|bloon|moab|bfb|zomg|ddt|sapper|alchemist|chinook|tetrimino|life experience|darwin|apotheosis/i.test(name)) return 'Towers & heroes';
  return 'Progression';
}
function renderAchievements() {
  const catalog = window.BLOONS_ACHIEVEMENTS.map(name => ({ id: `steam-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`, name, category: achievementCategory(name), hidden: hiddenAchievementNames.has(name) }));
  const entries = catalog;
  const statusOf = entry => {
    const observation = detectedProgress.achievements[entry.id];
    if (!observation || !['completed', 'working', 'todo'].includes(observation.status)) return 'unknown';
    if (!Number.isInteger(observation.percent) || observation.percent < 0 || observation.percent > 100) return 'unknown';
    if ((observation.status === 'completed') !== (observation.percent === 100)) return 'unknown';
    return observation.status;
  };
  const count = { completed: 0, working: 0, todo: 0, unknown: 0 };
  entries.forEach(entry => { count[statusOf(entry)]++; });
  const pct = entries.length ? Math.round(count.completed / entries.length * 100) : 0;
  document.querySelector('#achievement-progress-count').textContent = count.unknown === entries.length ? `— / ${entries.length}` : `${count.completed} / ${entries.length}`;
  document.querySelector('#achievement-progress-percent').textContent = count.unknown ? 'Scan pending' : `${pct}%`;
  document.querySelector('#achievement-progress-bar').style.width = `${pct}%`;
  document.querySelector('#achievement-done-count').textContent = count.completed;
  document.querySelector('#achievement-working-count').textContent = count.working;
  document.querySelector('#achievement-todo-count').textContent = count.todo;
  document.querySelector('#stat-achievements').textContent = count.unknown === entries.length ? '—' : count.completed;
  document.querySelector('#stat-achievements-pct').textContent = count.unknown === entries.length ? 'Detected game progress' : `${pct}% of ${entries.length} completed`;
  document.querySelector('#achievement-count').textContent = count.unknown ? '—' : count.todo + count.working;

  // Overview counters above remain live; hidden achievement cards need no DOM work.
  if (document.querySelector('#achievements')?.classList.contains('hidden')) return;

  const filters = document.querySelector('#achievement-categories'); filters.replaceChildren();
  const categories = ['All', ...achievementCategories];
  categories.forEach(category => {
    const total = category === 'All' ? entries.length : entries.filter(entry => entry.category === category).length;
    const button = document.createElement('button'); button.type = 'button'; button.className = `category-filter ${activeAchievementCategory === category ? 'active' : ''}`;
    button.textContent = `${category} ${total}`;
    button.addEventListener('click', () => { activeAchievementCategory = category; renderAchievements(); });
    filters.append(button);
  });
  const statusFilters = document.querySelector('#achievement-status-filters'); statusFilters.replaceChildren();
  achievementStatuses.forEach(status => {
    const button = document.createElement('button'); button.type = 'button'; button.className = `status-filter ${activeAchievementStatus === status ? 'active' : ''}`;
    button.textContent = status;
    button.addEventListener('click', () => { activeAchievementStatus = status; renderAchievements(); });
    statusFilters.append(button);
  });

  const list = document.querySelector('#achievement-list'); list.replaceChildren();
  const visible = entries.filter(entry => {
    const categoryMatch = activeAchievementCategory === 'All' || entry.category === activeAchievementCategory;
    const status = statusOf(entry);
    // Don't present missing cache rows as a reported achievement state.
    const statusMatch = status !== 'unknown' && (activeAchievementStatus === 'All status' || ({ 'To do': 'todo', 'In progress': 'working', 'Completed': 'completed' })[activeAchievementStatus] === status);
    const searchMatch = !achievementQuery || `${entry.name} ${entry.category}`.toLowerCase().includes(achievementQuery);
    return categoryMatch && statusMatch && searchMatch;
  });
  visible.forEach(entry => {
    const status = statusOf(entry);
    const observation = detectedProgress.achievements[entry.id];
    const entryPercent = Number.isInteger(observation?.percent) ? observation.percent : (status === 'completed' ? 100 : null);
    const row = document.createElement('article'); row.className = `achievement-card status-${status}`;
    row.innerHTML = `<span class="achievement-percent-ring"><svg viewBox="0 0 44 44"><circle class="ring-track" cx="22" cy="22" r="18"/><circle class="ring-fill" cx="22" cy="22" r="18"/></svg><b></b></span><div class="achievement-copy"><div class="achievement-name-line"><b></b><span class="achievement-category-chip"></span></div><small></small></div><span class="achievement-readonly status-chip"></span>`;
    row.querySelector('.achievement-copy b').textContent = entry.name;
    row.querySelector('.achievement-category-chip').textContent = entry.category;
    row.querySelector('.achievement-copy small').textContent = observation?.description || 'Game progress · read only';
    row.querySelector('.achievement-readonly').textContent = ({ completed: 'Completed', working: 'In progress', todo: 'To do' })[status];
    const ring = row.querySelector('.achievement-percent-ring');
    ring.querySelector('b').textContent = entryPercent == null ? '?' : `${entryPercent}%`;
    const CIRC = 2 * Math.PI * 18;
    const fill = ring.querySelector('.ring-fill');
    fill.style.strokeDasharray = `${CIRC}`;
    fill.style.strokeDashoffset = `${CIRC * (1 - (entryPercent ?? 0) / 100)}`;
    list.append(row);
  });
  document.querySelector('#achievement-empty').classList.toggle('hidden', visible.length > 0);
}

function renderRecentActivity() {
  const recent = document.querySelector('#recent-maps');
  if (!recent) return;
  const items = [];
  const activeStatus = latestAutomationStatus;
  const activeSweep = activeStatus?.progress?.blackBorderSweep;
  if (activeStatus?.running) {
    const currentMap = activeSweep?.currentMap || activeStatus.checkpoint?.map;
    const mapEntry = currentMap ? findMap(currentMap) : null;
    const mapName = mapEntry?.name || String(currentMap || 'Current route').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    const mode = activeSweep?.gamemode || activeStatus.checkpoint?.gamemode;
    const round = activeStatus.replay?.round;
    const checkpointMatches = activeStatus.checkpoint?.map === currentMap
      && (!mode || activeStatus.checkpoint?.gamemode === mode);
    const step = checkpointMatches ? activeStatus.checkpoint?.nextStep : null;
    const total = checkpointMatches ? activeStatus.checkpoint?.totalSteps : null;
    const live = document.createElement('div'); live.className = 'activity-live';
    const title = document.createElement('b'); title.textContent = `In progress · ${mapName}`;
    const detail = document.createElement('small');
    detail.textContent = [mode ? (MEDAL_BY_MODE[mode]?.[3] || mode.replace(/_/g, ' ')) : null,
      Number.isInteger(round) ? `Round ${round}` : null,
      Number.isInteger(step) && Number.isInteger(total) ? `Route ${step}/${total}` : null].filter(Boolean).join(' · ');
    live.append(title, detail); items.push(live);
  }
  const gains = (detectedProgress.medalGains || []).slice(0, 8);
  if (gains.length) {
    items.push(...gains.map(({ map, mode, at }) => {
      const entry = findMap(map) || { name: map.replace(/\b\w/g, c => c.toUpperCase()), category: 'Custom' };
      const item = document.createElement('span'); item.className = 'recent-map';
      const text = document.createElement('span'); text.className = 'recent-text';
      const title = document.createElement('b'); title.textContent = entry.name;
      const detail = document.createElement('small');
      // Automation stores ISO strings, while older progress files stored Unix
      // seconds or milliseconds. Normalize all forms before calculating age.
      const elapsed = sourceAgeMs(at);
      const ageSeconds = elapsed == null ? null : Math.floor(elapsed / 1000);
      if (ageSeconds == null) { detail.textContent = `${MEDAL_BY_MODE[mode]?.[3] || mode} medal · time unknown`; }
      const age = ageSeconds < 60 ? `${ageSeconds}s`
        : ageSeconds < 3600 ? `${Math.floor(ageSeconds / 60)}m`
        : ageSeconds < 86400 ? `${Math.floor(ageSeconds / 3600)}h ${Math.floor(ageSeconds % 3600 / 60)}m`
        : `${Math.floor(ageSeconds / 86400)}d`;
      if (ageSeconds != null) detail.textContent = `${MEDAL_BY_MODE[mode]?.[3] || mode} medal · ${age} ago`;
      text.append(title, detail);
      item.append(mapThumb(entry.name, entry.category), text, medalIcon(mode, true));
      return item;
    }));
  } else if (!items.length) {
    const empty = document.createElement('span'); empty.className = 'muted'; empty.textContent = 'No medals gained since Bloons+ started reading the game.';
    items.push(empty);
  }
  recent.replaceChildren(...items);
}

function render() {
  state.theme = state.theme === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = state.theme;
  renderMaps(); renderTowers(); renderAchievements(); renderBossHub();
  const remainingMapCount = Object.keys(detectedProgress.maps).length ? mapChoices.filter(map => !isMapDone(map.name)).length : '—';
  document.querySelector('#stat-queue').textContent = remainingMapCount;
  document.querySelector('#queue-count').textContent = remainingMapCount;
  document.querySelector('#stat-completed').textContent = Object.keys(detectedProgress.maps).length ? Object.values(detectedProgress.maps).filter(map => map.blackBorder).length : '—';
  const next = mapChoices.find(map => mapObservationFor(map.name)?.medals && !isMapDone(map.name));
  document.querySelector('#stat-next').textContent = next ? `Next: ${next.name}` : 'Waiting for a map scan';
  const active = document.querySelector('#active-time');
  if (active) {
    const minutes = Math.max(0, Math.floor((Date.now() - appOpenedAt) / 60000));
    active.textContent = `Active ${minutes < 60 ? `${minutes}m` : `${Math.floor(minutes / 60)}h ${minutes % 60}m`}`;
  }
  renderRecentActivity();
  const local = detectedProgress.localSave;
  const localAvailable = detectedProgress.localProfile?.available === true;
  const localStatus = document.querySelector('#local-save-status');
  if (localStatus) localStatus.textContent = localAvailable ? 'VM CONNECTED' : local?.source === 'vm-unavailable' ? 'VM OFFLINE' : 'NOT CONNECTED';
  const localRaw = detectedProgress.localProfile || {};
  const setText = (selector, value) => { const node = document.querySelector(selector); if (node) node.textContent = value; };
  const upgradeCount = Array.isArray(localRaw.acquiredUpgrades) ? localRaw.acquiredUpgrades.length : 0;
  setText('#stat-upgrades', localAvailable ? upgradeCount.toLocaleString() : '—');
  setText('#stat-upgrades-source', localAvailable ? 'Unlocked in game save' : 'Waiting for game save');
  setText('#local-rank', localAvailable ? localRaw.rank ?? '—' : '—');
  setText('#local-veteran-rank', localAvailable ? localRaw.veteranRank ?? '—' : '—');
  setText('#local-monkey-money', localAvailable && Number.isFinite(localRaw.monkeyMoney) ? localRaw.monkeyMoney.toLocaleString() : '—');
  const towerCount = Object.keys(localRaw.towerXp || {}).length;
  const mapCount = Object.keys(localRaw.mapProgress || {}).length;
  setText('#local-coverage', localAvailable ? `${towerCount} towers · ${mapCount} maps` : '—');
  const hotkeys = localAvailable ? localRaw.hotkeyReport : null;
  const hotkeyList = document.querySelector('#hotkey-report');
  if (hotkeyList) {
    setText('#hotkey-report-summary', !hotkeys ? 'Hotkeys not read yet.'
      : hotkeys.missing.length ? `${hotkeys.missing.length} action(s) the automation uses have no hotkey. Bind them in BTD6 → Settings → Hotkeys:`
        : `All ${hotkeys.total} hotkeys the automation uses are bound. Changes in BTD6 apply from the next route.`);
    setText('#hotkey-report-chip', !hotkeys ? 'READ ONLY' : hotkeys.missing.length ? `${hotkeys.missing.length} MISSING` : 'ALL BOUND');
    hotkeyList.replaceChildren(...(hotkeys?.missing || []).map(item => {
      const row = document.createElement('small');
      row.textContent = `${item.action} → ${item.recommended || 'any free key'}`;
      return row;
    }));
  }
  setText('#local-save-read', local?.readAt ? `Last save read ${new Date(local.readAt).toLocaleTimeString()}` : 'Last save read —');
  document.querySelectorAll('#theme-setting input[name="app-theme"]').forEach(input => { input.checked = input.value === state.theme; });
  const introChoice=document.querySelector('#startup-mode');
  if(introChoice)introChoice.value=['full','reduced','off'].includes(state.startupMode)?state.startupMode:'full';
  window.refreshSelectControls?.();
  const player = detectedProgress.player;
  // Profile.Save is rewritten by BTD6 continuously; the menu-screen scan only refreshes when
  // the main menu is visible, so it goes stale during a sweep. Prefer the save.
  const saveRank = localAvailable && Number.isFinite(localRaw.rank) ? localRaw.rank : null;
  setText('#player-level', saveRank ?? (player?.level != null && player.level !== '—' ? player.level : '—'));
  setText('#player-veteran', localAvailable && Number.isFinite(localRaw.veteranRank) ? localRaw.veteranRank
    : player?.veteran != null && player.veteran !== '—' ? player.veteran : '—');
  const savedXp = localAvailable ? window.BloonsPlayerXp.saveLevelProgress(localRaw) : null;
  // A readable save is authoritative. Do not replace a mismatched save with stale OCR.
  const scannedXpValid = !localAvailable && Number.isFinite(player?.xp) && Number.isFinite(player?.nextLevelXp)
    && player.nextLevelXp > 0 && player.xp >= 0 && player.xp <= player.nextLevelXp;
  const xpProgress = savedXp || (scannedXpValid ? { xp: player.xp, nextLevelXp: player.nextLevelXp, remaining: player.nextLevelXp - player.xp } : null);
  const xpBar = document.querySelector('#player-xp-bar');
  if (xpBar) xpBar.style.width = xpProgress?.capped ? '100%' : xpProgress ? `${Math.min(100, xpProgress.xp / xpProgress.nextLevelXp * 100)}%` : '0%';
  setText('#player-xp', xpProgress?.capped ? 'Level cap reached · veteran progression' : xpProgress
    ? `${Math.ceil(xpProgress.remaining).toLocaleString()} XP to next level` : 'XP not verified');
  const formatRate = value => Number.isFinite(value) ? `${(Math.round(value) || 0).toLocaleString()}` : '—';
  const formatTime = hours => {
    if (!Number.isFinite(hours) || hours <= 0) return '—';
    if (hours < 1) return `${Math.max(1, Math.round(hours * 60))}m`;
    if (hours < 48) return `${hours.toFixed(1)}h`;
    return `${(hours / 24).toFixed(1)}d`;
  };
  const xpRate = localAvailable ? profileRates.xpPerHour : player?.xpPerHour;
  const moneyRate = localAvailable ? profileRates.monkeyMoneyPerHour : player?.monkeyMoneyPerHour;
  const xpRemaining = xpProgress && !xpProgress.capped ? xpProgress.remaining : NaN;
  const monkeyMoney = Number.isFinite(localRaw.monkeyMoney) ? localRaw.monkeyMoney : player?.monkeyMoney;
  setText('#player-monkey-money', Number.isFinite(monkeyMoney) ? monkeyMoney.toLocaleString() : '—');
  setText('#player-monkey-money-rate', Number.isFinite(moneyRate) ? formatRate(moneyRate) : '—');
  setText('#player-xp-rate', Number.isFinite(xpRate) ? formatRate(xpRate) : '—');
  setText('#player-level-time', Number.isFinite(xpRate) && xpRate > 0 ? formatTime(xpRemaining / xpRate) : '—');
  const syncLabel = liveSyncLabel();
  setText('#player-sync', syncLabel.title);
  const mapTitle = document.querySelector('#map-sync-title'), mapDetail = document.querySelector('#map-sync-detail');
  if (mapTitle) { mapTitle.textContent = syncLabel.title; if (mapDetail) mapDetail.textContent = syncLabel.detail; }
  const towerTitle = document.querySelector('#tower-sync-title'), towerDetail = document.querySelector('#tower-sync-detail');
  if (towerTitle) { towerTitle.textContent = syncLabel.title; if (towerDetail) towerDetail.textContent = 'Profile and live-scan reads are shown with their source time.'; }
}
function liveSyncLabel() {
  const profileReadAt = detectedProgress.localSave?.readAt;
  if (profileReadAt) {
    const elapsed = sourceAgeMs(profileReadAt);
    const seconds = elapsed == null ? null : Math.round(elapsed / 1000);
    return { title: seconds == null ? 'VM profile save · time unavailable' : `VM profile save · updated ${seconds}s ago`, detail: 'Tower XP, map medals, and profile totals come from the read-only BTD6 save inside the VM.' };
  }
  if (detectedProgress.localSave?.source === 'vm-unavailable') return { title: 'VM save unavailable', detail: detectedProgress.localSave.reason || 'Waiting for the VM profile-save reader.' };
  if (detectedProgress.source === 'live-scan') {
    const elapsed = sourceAgeMs(detectedProgress.capturedAt);
    const seconds = elapsed == null ? null : Math.round(elapsed / 1000);
    const screen = detectedProgress.lastRecognizedScreen;
    return { title: seconds != null ? `Live scan · updated ${seconds}s ago` : 'Live scan', detail: screen && screen !== 'unknown' ? `Reading the ${screen} screen.` : 'Waiting for a recognized game screen.' };
  }
  if (detectedProgress.source === 'calibration-snapshot') return { title: 'Calibration snapshot · not live', detail: 'A saved snapshot. Connect the game to refresh your current progress.' };
  return { title: 'Waiting for game progress', detail: 'Check the game connection in Settings. Progress refreshes automatically from your save.' };
}

function markVmSaveUnavailable(payload = {}) {
  detectedProgress.localSave = { source: 'vm-unavailable', reason: payload.reason || 'VM profile save is unavailable.' };
  detectedProgress.localProfile = { available: false, source: 'vm-unavailable' };
  if (detectedProgress.player) {
    detectedProgress.player = { ...detectedProgress.player };
    delete detectedProgress.player.monkeyMoney;
  }
  render();
}

// Both progress pollers share a save read. Reapply the newest completed read
// after slower scanner/catalog requests, never an earlier response's profile.
let pendingLocalSaveRead = null;
let latestLocalSaveRead = null;
let localSaveReadSequence = 0;
function currentLocalSaveRead(read) {
  return latestLocalSaveRead && latestLocalSaveRead.sequence > read.sequence ? latestLocalSaveRead : read;
}
function readLocalSaveProgress() {
  if (pendingLocalSaveRead) return pendingLocalSaveRead;
  const sequence = ++localSaveReadSequence;
  pendingLocalSaveRead = (async () => {
    const response = await fetch('/api/progress/local-save', { cache: 'no-store', signal: AbortSignal.timeout(10000) });
    const profile = response.ok || response.status === 503 ? await response.json() : null;
    const read = { sequence, ok: response.ok, status: response.status, profile };
    latestLocalSaveRead = read;
    return read;
  })().finally(() => { pendingLocalSaveRead = null; });
  return pendingLocalSaveRead;
}
async function loadDetectedProgress() {
  try {
    const [response, upgradeResponse, gameStateResponse, localSaveResponse, towerCatalogResponse] = await Promise.all([
      fetch('/api/progress', { cache: 'no-store', signal: AbortSignal.timeout(10000) }),
      fetch('/api/upgrade-memory', { cache: 'no-store', signal: AbortSignal.timeout(10000) }),
      fetch('/api/game-state', { cache: 'no-store', signal: AbortSignal.timeout(10000) }),
      readLocalSaveProgress(),
      fetch('/api/tower-upgrade-catalog', { cache: 'no-store', signal: AbortSignal.timeout(10000) }).catch(() => null),
    ]);
    if (towerCatalogResponse?.ok) towerUpgradeCatalog = await towerCatalogResponse.json();
    else {
      const fallback = await fetch('/btd6bot/btd6bot/Files/upgrades_current.json', { cache: 'no-store', signal: AbortSignal.timeout(10000) }).catch(() => null);
      if (fallback?.ok) towerUpgradeCatalog = await fallback.json();
      const overrides = await fetch('/data/config/tower-upgrade-overrides.json', { cache: 'no-store', signal: AbortSignal.timeout(10000) }).catch(() => null);
      if (overrides?.ok) Object.assign(towerUpgradeCatalog, await overrides.json());
    }
    if (upgradeResponse.ok) {
      const ledger = await upgradeResponse.json();
      if (ledger && typeof ledger.runs === 'object') routeUpgradeMemory = ledger;
      renderTowers();
    }
    if (gameStateResponse.ok) {
      const snapshot = await gameStateResponse.json();
      latestGameState = snapshot?.state === null ? null : snapshot;
      renderGameState();
      renderTowers();
    }
    if (!response.ok) return;
    const snapshot = await response.json();
    if (!['calibration-snapshot', 'live-scan'].includes(snapshot.source) || !snapshot.maps || !snapshot.towers || !snapshot.achievements) return;
    detectedProgress = snapshot;
    const saveRead = currentLocalSaveRead(localSaveResponse);
    if (saveRead.ok) {
      const localSave = saveRead.profile;
      if (localSave.available) {
        observeProfileRates(localSave);
        detectedProgress.localSave = { source: localSave.source, readAt: localSave.readAt };
        detectedProgress.localProfile = localSave;
        if (Number.isFinite(localSave.monkeyMoney)) detectedProgress.player = { ...(detectedProgress.player || {}), monkeyMoney: localSave.monkeyMoney };
        detectedProgress.heroes = localSave.heroes || detectedProgress.heroes || {};
        renderProfileUnlocks();
        for (const [name, xp] of Object.entries(localSave.towerXp || {})) {
          if (typeof xp !== 'number' && typeof xp !== 'string') continue;
          const displayName = Object.values(TOWER_NAMES).find(label => label.toLowerCase().replace(/[^a-z0-9]/g, '') === name.toLowerCase().replace(/[^a-z0-9]/g, '')) || name;
          const current = detectedProgress.towers[displayName] || {};
          detectedProgress.towers[displayName] = { ...current, xp: Number(xp), xpSource: 'btd6-profile-save', xpVerifiedAt: localSave.readAt };
        }
        // Preserve the decoded map structure for the UI and future field-specific mapping.
        detectedProgress.localMapProgress = localSave.mapProgress || {};
        for (const [rawName, record] of Object.entries(localSave.mapProgress || {})) {
          const key = rawName.toLowerCase().replace(/[^a-z0-9]+/g, '');
          const existing = detectedProgress.maps[key] || {};
          const modes = {};
          for (const [difficulty, data] of Object.entries(record?.difficult || {})) {
            for (const [mode, value] of Object.entries(data?.modes || {})) modes[`${difficulty}:${mode}`] = value;
          }
          const localMedals = medalsFromLocalRecord(record);
          detectedProgress.maps[key] = { ...existing, medals: { ...(existing.medals || {}), ...localMedals },
            blackBorder: MEDAL_SLOTS.every(([mode]) => localMedals[mode] === true), localSaveRecord: record, localModes: modes,
            localSaveSource: 'btd6-profile-save', localSaveReadAt: localSave.readAt };
        }
      } else markVmSaveUnavailable(localSave);
    } else if (saveRead.status === 503) {
      markVmSaveUnavailable(saveRead.profile || {});
    }
    applySteamAchievements();
    render();
    renderSpecificMapRequirements();
  } catch { /* Preserve the last readable snapshot when the connector is offline. */ }
}
// Profile.Save is independent of screen scanning. Refresh it on its own cadence so tower XP
// and map progress update shortly after Steam writes a new save, without waiting for a menu scan.
async function refreshLocalSaveProgress() {
  try {
    const response = currentLocalSaveRead(await readLocalSaveProgress());
    if (!response.ok) {
      if (response.status === 503) markVmSaveUnavailable(response.profile || {});
      return;
    }
    const localSave = response.profile;
    if (!localSave.available) { markVmSaveUnavailable(localSave); return; }
    observeProfileRates(localSave);
    detectedProgress.localSave = { source: localSave.source, readAt: localSave.readAt };
    detectedProgress.localProfile = localSave;
    if (Number.isFinite(localSave.monkeyMoney)) detectedProgress.player = { ...(detectedProgress.player || {}), monkeyMoney: localSave.monkeyMoney };
    detectedProgress.heroes = localSave.heroes || detectedProgress.heroes || {};
    renderProfileUnlocks();
    detectedProgress.towers ||= {};
    for (const [name, xp] of Object.entries(localSave.towerXp || {})) {
      if (typeof xp !== 'number' && typeof xp !== 'string') continue;
      const displayName = Object.values(TOWER_NAMES).find(label => label.toLowerCase().replace(/[^a-z0-9]/g, '') === name.toLowerCase().replace(/[^a-z0-9]/g, '')) || name;
      detectedProgress.towers[displayName] = { ...(detectedProgress.towers[displayName] || {}), xp: Number(xp),
        xpSource: 'btd6-profile-save', xpVerifiedAt: localSave.readAt };
    }
    detectedProgress.localMapProgress = localSave.mapProgress || {};
    for (const [rawName, record] of Object.entries(localSave.mapProgress || {})) {
      const key = rawName.toLowerCase().replace(/[^a-z0-9]+/g, '');
      const modes = {};
      for (const [difficulty, data] of Object.entries(record?.difficult || {})) {
        for (const [mode, value] of Object.entries(data?.modes || {})) modes[`${difficulty}:${mode}`] = value;
      }
      const existing = detectedProgress.maps[key] || {};
      const localMedals = medalsFromLocalRecord(record);
      detectedProgress.maps[key] = { ...existing, medals: { ...(existing.medals || {}), ...localMedals },
        blackBorder: MEDAL_SLOTS.every(([mode]) => localMedals[mode] === true), localSaveRecord: record,
        localModes: modes, localSaveSource: 'btd6-profile-save', localSaveReadAt: localSave.readAt };
    }
    render();
    renderSpecificMapRequirements();
  } catch { /* local save is optional while Steam/VM is unavailable */ }
}
const achievementIdOf = name => `steam-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
// Achievement completion read straight from Steam's own local achievement cache (steam-progress.js
// on the server side) instead of OCR-scanning the in-game achievements screen. Steam's cache only
// covers achievements, not maps or tower XP, so those stay on the existing live-scan path.
// Kept separate from detectedProgress (which loadDetectedProgress replaces wholesale every 5s from
// /api/progress) so a full-progress poll can never silently wipe out this merge until the next
// 20s Steam poll happens to run again.
let steamAchievementEntries = null;
function applySteamAchievements() {
  if (!steamAchievementEntries) return;
  detectedProgress.achievements ||= {};
  Object.assign(detectedProgress.achievements, steamAchievementEntries);
}
async function loadSteamAchievements() {
  try {
    const response = await fetch('/api/achievements/steam', { cache: 'no-store', signal: AbortSignal.timeout(8000) });
    if (!response.ok) return;
    const result = await response.json();
    const banner = document.querySelector('#achievement-source-note');
    if (banner) banner.textContent = result.available
      ? result.hostFallback
        ? 'Read from this PC’s Steam cache; the VM cache is not reachable yet.'
        : result.sourceTransport === 'vm'
          ? 'Read from the VM’s Steam achievement cache.'
          : 'Read from Steam’s local achievement cache.'
      : `Steam achievement cache unavailable: ${result.reason || 'unknown reason'}.`;
    if (!result.available) return;
    const entries = {};
    for (const achievement of result.achievements) {
      const percent = achievement.unlocked ? 100
        : achievement.progress ? Math.max(0, Math.min(99, Math.floor(achievement.progress.current / (achievement.progress.target || 1) * 100)))
        : 0;
      entries[achievementIdOf(achievement.name)] = {
        status: achievement.unlocked ? 'completed' : percent > 0 ? 'working' : 'todo',
        percent, source: 'steam-local', unlockedAt: achievement.unlockedAt,
        progress: achievement.progress, description: achievement.description,
      };
    }
    steamAchievementEntries = entries;
    applySteamAchievements();
    renderAchievements();
  } catch { /* Steam cache is optional; keep the last confirmed values. */ }
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
document.querySelectorAll('[data-go]').forEach(button => button.addEventListener('click', () => showView(button.dataset.go)));
document.querySelector('#maps-search').addEventListener('input', renderMaps);
document.querySelector('#maps-hide-done').addEventListener('change', renderMaps);
document.querySelector('#achievement-search').addEventListener('input', event => { achievementQuery = event.target.value.trim().toLowerCase(); renderAchievements(); });
document.querySelector('#theme-setting')?.addEventListener('change', event => {
  if (!event.target.matches('input[name="app-theme"]')) return;
  state.theme = event.target.value === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = state.theme;
  saveState();
  notify(`${state.theme === 'dark' ? 'Dark' : 'Light'} mode enabled.`);
});
let connectionPending = false;
document.querySelector('#startup-mode')?.addEventListener('change',event=>{
  state.startupMode=['full','reduced','off'].includes(event.target.value)?event.target.value:'full';saveState();
});
async function refreshConnection(manual = false) {
  if (connectionPending) return;
  connectionPending = true;
  const button = document.querySelector('#refresh-connection');
  const label = document.querySelector('#connection-label');
  button.disabled = true;
  if (manual) label.textContent = 'Looking for BTD6…';
  try {
    const response = await fetch('/api/game-status', { cache: 'no-store', signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error();
    const game = await response.json();
    label.textContent = game.running ? 'Game found · scanning' : 'BTD6 is not running';
    if (!detectedProgress.capturedAt) document.querySelector('#player-sync').textContent = game.running ? 'Game found · reading screen' : 'Waiting for game data';
    document.querySelector('.rail-bottom .connection-dot').style.background = game.running ? '#6d9a87' : '';
    if (manual) notify(game.running ? 'BTD6 found. Live screen scanning is running.' : 'Open BTD6 on Steam, then check again.');
  } catch {
    label.textContent = 'Detection unavailable';
    if (manual) notify('Game detection is unavailable. Restart Bloons+ to load its connector.');
  } finally { connectionPending = false; button.disabled = false; }
}
document.querySelector('#refresh-connection').addEventListener('click', () => refreshConnection(true));
refreshConnection();
setInterval(() => { if (!document.hidden) refreshConnection(); }, 15000);
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !event.defaultPrevented && !document.querySelector('dialog[open]')) showView('overview');
});
render();
try {
  const lastView = localStorage.getItem('bloonsplus-last-view');
  if (lastView && document.getElementById(lastView)) showView(lastView);
} catch { /* private/blocked storage: default view stands */ }
loadDetectedProgress();
setInterval(() => { if (!document.hidden) loadDetectedProgress(); }, 5000);
refreshLocalSaveProgress();
setInterval(() => { if (!document.hidden) refreshLocalSaveProgress(); }, 10000);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) { loadDetectedProgress(); refreshLocalSaveProgress(); }
});
loadSteamAchievements();
setInterval(() => { if (!document.hidden) loadSteamAchievements(); }, 20000);

const FINAL_ROUNDS = { easy: 40, primary_only: 40, deflation: 60, medium: 60, military_only: 60, reverse: 60, apopalypse: 60, hard: 80, magic_monkeys_only: 80, double_hp_moabs: 80, half_cash: 80, alternate_bloons_rounds: 80, impoppable: 100, chimps: 100 };
// Overview's run panel: the same status as the Automation tab, readable at a glance. The log shows
// only events (routes, medals, warnings), not the per-frame cash reads.
function renderRunConsole(status) {
  const chip = document.querySelector('#run-chip'); if (!chip) return;
  const sweep = status.progress?.blackBorderSweep;
  const mode = status.running ? (sweep?.gamemode || status.checkpoint?.gamemode) : null;
  const inRound = status.running && status.replay?.screen === 'INGAME';
  chip.textContent = status.statusUnavailable ? 'CHECKING VM' : status.running ? (status.stopping ? 'STOPPING' : inRound ? 'PLAYING' : 'NAVIGATING') : 'IDLE';
  document.querySelector('#run-where').textContent = status.statusUnavailable ? 'VM status unavailable · reconnecting; automation controls are locked.' : status.statusStale ? 'VM status reconnecting · showing the last confirmed run.' : status.vm ? 'Running in the Bloons+ VM · this PC stays free.' : 'Running on this PC.';
  document.querySelector('#run-map').textContent = status.running && sweep?.currentMap ? sweep.currentMap.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : '—';
  document.querySelector('#run-round').textContent = status.running && status.replay?.round != null ? `${status.replay.round} / ${FINAL_ROUNDS[mode] || '—'}` : '— / —';
  document.querySelector('#run-mode').textContent = status.running ? `${status.type.replace(/-/g, ' ')}${mode ? ` · ${MEDAL_BY_MODE[mode]?.[3] || mode}` : ''}` : 'Idle';
  const elapsed = status.running ? sourceAgeMs(status.startedAt) : null;
  const minutes = elapsed == null ? null : Math.floor(elapsed / 60000);
  document.querySelector('#run-time').textContent = minutes == null ? '—' : minutes < 60 ? `${minutes}m` : `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
  const runLog = status.log || [];
  const victoryCount = Number.isFinite(status.victories) ? status.victories : runLog.filter(line => /VICTORY_CONFIRMED\b/.test(line)).length;
  const defeatCount = Number.isFinite(status.defeats) ? status.defeats : runLog.filter(line => /screen DEFEAT!/.test(line)).length;
  document.querySelector('#run-victories').textContent = String(victoryCount);
  document.querySelector('#run-defeats').textContent = String(defeatCount);
  document.querySelector('#run-stop').disabled = !status.running;
  const overviewStopAfter = document.querySelector('#run-stop-after');
  if (overviewStopAfter) {
    overviewStopAfter.disabled = !status.running || !!status.stopAfterReplay;
    overviewStopAfter.textContent = status.stopAfterReplay ? 'Stops after this replay' : 'Stop after replay';
  }
  document.querySelector('#run-start').disabled = status.running || !!status.busyWith;
  const events = (status.log || []).filter(line => !/DEBUG|detected money|detected round|OCR values/.test(line)).slice(-8);
  document.querySelector('#run-log').textContent = events.join('\n');
  const resultChip = document.querySelector('#run-result');
  if (resultChip) {
    const result = latestGameState?.result;
    const ageMs = sourceAgeMs(latestGameState?.updatedAt);
    // Only worth showing while it's the outcome of the run that just ended, not an old snapshot.
    const resultMatchesRun = !status.running || (latestGameState?.map === sweep?.currentMap
      && latestGameState?.mode === mode);
    const fresh = ageMs != null && ageMs < 3 * 60000 && !inRound && resultMatchesRun;
    if (fresh && (result === 'victory' || result === 'defeat')) {
      resultChip.classList.remove('hidden', 'result-victory', 'result-defeat');
      resultChip.classList.add(result === 'victory' ? 'result-victory' : 'result-defeat');
      const mapName = (latestGameState.map || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      resultChip.textContent = `${result === 'victory' ? '✓ VICTORY' : '✕ DEFEAT'}${mapName ? ` · ${mapName}` : ''}`;
    } else {
      resultChip.classList.add('hidden');
    }
  }
}
function renderAutomationStatus(status) {
  latestAutomationStatus = status;
  try { renderRecentActivity(); } catch (error) { console.warn('Activity rendering failed:', error); }
  const detail = document.querySelector('#automation-status-detail');
  if (!detail) return;
  const outcomes = `${Number.isInteger(status.victories) && status.victories >= 0 ? status.victories : 0} victories · ${Number.isInteger(status.defeats) && status.defeats >= 0 ? status.defeats : 0} defeats`;
  const recentOutcome = (status.log || []).slice().reverse().find(line => /victory|defeat|ROUTE_FAILURE|objective failed/i.test(line));
  detail.textContent = status.statusUnavailable ? 'VM status unavailable · reconnecting; start is temporarily locked'
    : status.stopping ? 'Stopping replay · waiting for the input process to exit'
    : status.running ? `${status.replay?.screen === 'INGAME' ? 'Playing' : 'Navigating'}: ${status.type}${status.replay?.round != null ? ` · round ${status.replay.round}` : ''} · ${outcomes}`
    : status.busyWith ? `Waiting — ${status.busyWith} automation task is running`
    : status.exitCode && status.exitCode !== 0 ? `Last run stopped with code ${status.exitCode} · see log below`
    : status.runtime?.available === false ? `AutoBTD6 needs ${status.runtime.missing}`
    : `Idle · ${outcomes}`;
  if (status.statusStale) detail.textContent = `VM reconnecting · last confirmed active run${status.replay?.round != null ? ` · round ${status.replay.round}` : ''}`;
  if (recentOutcome && status.running) detail.textContent += ` · ${recentOutcome.replace(/^.*?\]\s*/, '').slice(0, 160)}`;
  document.querySelector('#automation-stop').disabled = !status.running;
  const stopAfterButton = document.querySelector('#automation-stop-after');
  if (stopAfterButton) {
    stopAfterButton.disabled = !status.running || !!status.stopAfterReplay;
    stopAfterButton.textContent = status.stopAfterReplay ? 'Stops after this replay' : 'Stop after replay';
  }
  const pauseButton = document.querySelector('#automation-pause');
  if (pauseButton) { pauseButton.disabled = !status.running; pauseButton.textContent = status.paused ? 'Resume' : 'Pause'; }
  const resumeButton = document.querySelector('#farm-resume');
  if (resumeButton) resumeButton.disabled = status.checkpoint?.status !== 'ready' || status.running || !!status.busyWith;
  for (const id of ['farm-xp', 'farm-mm', 'farm-max-towers', 'farm-achievements', 'farm-blackborder']) {
    const button = document.querySelector(`#${id}`);
    if (button) button.disabled = status.runtime?.available === false || status.running || !!status.busyWith;
  }
  syncSelectedRunButton();
  const logLines = keepRunLog(status);
  latestRunLog = logLines.join('\n');
  const compactLog = logLines.slice(-120).join('\n') || 'No run output yet.';
  const visibleLog = logLines.slice(-2000).join('\n') || 'No run output yet.';
  const compactNode = document.querySelector('#automation-log');
  const fullNode = document.querySelector('#full-log');
  if (compactNode.textContent !== compactLog) compactNode.textContent = compactLog;
  if (fullNode.textContent !== visibleLog) fullNode.textContent = visibleLog;
  document.querySelector('#full-log-title').textContent = status.running ? 'Live run' : 'Latest run';
  document.querySelector('#full-log-detail').textContent = `${logLines.length} lines · ${status.type || 'No run'}${status.vm ? ' · VM' : ''}`;
  if (!status.running && status.checkpoint?.status === 'ready') {
    detail.textContent += ` · Interrupted ${status.checkpoint.map} / ${status.checkpoint.gamemode} at step ${status.checkpoint.nextStep}/${status.checkpoint.totalSteps}`;
  } else if (!status.running && status.checkpoint?.status === 'pending') {
    detail.textContent += ' · Replay stopped during an input; check the game before restarting this route';
  }
  // The compact Overview panel can differ across packaged versions. Keep the
  // primary Automation status current even if one of its optional widgets fails.
  try { renderRunConsole(status); } catch (error) { console.warn('Run overview rendering failed:', error); }
  const sweepDetail = document.querySelector('#sweep-progress');
  const sweep = status.progress?.blackBorderSweep;
  if (sweepDetail && sweep) {
    const active = status.running && status.type === 'black-border-sweep';
    const state = active ? (status.stopping ? 'Stopping' : 'Running')
      : sweep.status === 'running' ? 'Interrupted · ready to resume' : sweep.status === 'complete' ? 'Pass finished' : 'Saved sweep';
    const location = [sweep.currentMap?.replace(/_/g, ' '), sweep.gamemode?.replace(/_/g, ' ')].filter(Boolean).join(' / ');
    sweepDetail.textContent = `${state} · Expert → Beginner · map ${sweep.mapIndex || 0}/${sweep.mapsTotal || 0}${location ? ` · ${location}` : ''} · ${sweep.counts?.confirmed || 0} clears this pass · ${sweep.counts?.incompleteMaps || 0} maps left incomplete${sweep.reason ? ` · ${sweep.reason.replace(/-/g, ' ')}` : ''}`;
  }
}
async function loadAutomationStatus() {
  if (automationStatusLoading) return;
  automationStatusLoading = true;
  try {
    const requestedAt = Date.now();
    const response = await fetch('/api/farm/status?view=ui', { cache: 'no-store', signal: AbortSignal.timeout(8000) });
    if (response.ok) {
      const status = await response.json();
      observeSourceClock(status, requestedAt, Date.now());
      renderAutomationStatus(status);
      // Re-read Profile.Save as soon as a run ends so XP, medals, heroes and
      // profile counters reflect the completed replay immediately.
      const endedAt = Number(status.endedAt || 0);
      if (!status.running && endedAt > lastRunRefreshAt) {
        lastRunRefreshAt = endedAt;
        // Treat the end of every run as a small update boundary: pull all
        // progress sources and route metadata before the next run can start.
        refreshLocalSaveProgress();
        loadDetectedProgress();
        loadSteamAchievements();
      }
    }
  } catch { /* connector offline */ }
  finally { automationStatusLoading = false; }
}
async function startFarmJob(body) {
  try {
    const response = await fetch('/api/farm/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const result = await response.json();
    notify(result.error ? `Could not start: ${result.error}` : result.queued ? result.message : 'Automation started.');
    loadAutomationStatus();
  } catch { notify('Could not reach the automation connector.'); }
}
document.querySelector('#copy-run-log')?.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(latestRunLog); notify('Run log copied.'); }
  catch { notify('Could not copy. Select the log text and copy it.'); }
});
document.querySelector('#download-run-log')?.addEventListener('click', () => {
  const blob = new Blob([latestRunLog || 'No run output yet.'], { type: 'text/plain' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `bloons-plus-run-${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
});
let latestRouteFailuresLog = '';
function formatRouteFailures(failures, includeFullLog = false) {
  return failures.slice().sort((a,b) => Number(b.actionable) - Number(a.actionable)).map(f => {
    const summary = `${f.at} | ${f.map} | ${f.gamemode} | ${f.route} | [${f.category || 'uncategorized'}] `
      + `round ${f.lastRound ?? '?'}/${f.finalRound ?? '?'} | lives ${f.livesLeft ?? '?'} | ${f.reason || 'unknown reason'}`;
    const full = includeFullLog && Array.isArray(f.fullLog) && f.fullLog.length
      ? `\n  --- full run log (${f.fullLog.length} lines) ---\n` + f.fullLog.map(line => `  ${line}`).join('\n') + '\n' : '';
    return summary + full;
  }).join('\n');
}
async function loadRouteFailures() {
  const pre = document.querySelector('#route-failures-log');
  const detail = document.querySelector('#route-failures-detail');
  try {
    const response = await fetch('/api/route-failures?view=ui', { cache: 'no-store', signal: AbortSignal.timeout(12000) });
    const body = await response.json().catch(() => null);
    const failures = body?.failures || [];
    if (!body?.available) {
      pre.textContent = body?.reason || 'Route failures are not available right now.';
      detail.textContent = 'Waiting for the VM';
      latestRouteFailuresLog = '';
      return;
    }
    // Sort real bugs (route-corruption, navigation-bug, insufficient-data) before ordinary
    // gameplay-defeats - a clean loss needs a better strategy, not a code fix, so it shouldn't bury
    // the entries that are actually actionable tonight.
    const ordered = failures.slice().sort((a, b) => Number(b.actionable) - Number(a.actionable));
    const actionableCount = ordered.filter(f => f.actionable).length;
    latestRouteFailuresLog = formatRouteFailures(ordered);
    pre.textContent = latestRouteFailuresLog || 'No route failures recorded yet.';
    const categoryCounts = failures.reduce((counts, failure) => {
      const category = failure.category || 'uncategorized';
      counts[category] = (counts[category] || 0) + 1;
      return counts;
    }, {});
    const breakdown = Object.entries(categoryCounts).sort((a, b) => b[1] - a[1])
      .map(([category, count]) => `${count} ${category}`).join(' · ');
    detail.textContent = `${failures.length} recorded failure${failures.length === 1 ? '' : 's'} `
      + `(${actionableCount} actionable). ${breakdown || 'No categories yet.'}`;
  } catch { pre.textContent = 'Could not reach the automation connector.'; detail.textContent = ''; }
}
document.querySelector('#download-route-failures')?.addEventListener('click', async event => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    const response = await fetch('/api/route-failures', {cache:'no-store', signal:AbortSignal.timeout(60000)});
    const body = await response.json();
    if (!response.ok || !body?.available) throw new Error(body?.reason || 'VM logs are unavailable');
    const text = formatRouteFailures(body.failures || [], true);
    const blob = new Blob([text || 'No route failures recorded yet.'], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `bloons-plus-route-failures-${new Date().toISOString().replace(/[:.]/g, '-')}.log`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  } catch { notify('Could not download full logs. Check the VM connection and try again.'); }
  finally { button.disabled = false; }
});
document.querySelector('#farm-file').addEventListener('click', () => {
  const mapSlug = document.querySelector('#playthrough-map-select').value;
  const gamemode = document.querySelector('#playthrough-variation-select').value;
  const entries = comboData[mapSlug]?.[gamemode];
  if (!mapSlug || !gamemode || !entries?.length) return notify('Pick a map and gamemode first.');
  const entry = entries[0];
  startFarmJob({ type: 'file', file: entry.filename, gamemode });
});
document.querySelector('#run-start').addEventListener('click', () => startFarmJob({ type: 'black-border-sweep' }));
document.querySelector('#run-stop').addEventListener('click', () => document.querySelector('#automation-stop').click());
document.querySelector('#run-stop-after')?.addEventListener('click', () => document.querySelector('#automation-stop-after')?.click());
document.querySelector('#automation-stop-after')?.addEventListener('click', async () => {
  try {
    const response = await fetch('/api/farm/stop-after', { method: 'POST' });
    const result = await response.json();
    notify(result.error ? `Could not schedule stop: ${result.error}` : 'The current replay will finish, then automation will stop.');
  } catch { notify('Could not reach the automation connector.'); }
  loadAutomationStatus();
});
document.querySelector('#automation-stop').addEventListener('click', async () => {
  try { await fetch('/api/farm/stop', { method: 'POST' }); notify('Stopping…'); } catch { notify('Could not reach the automation connector.'); }
  loadAutomationStatus();
});
document.querySelector('#automation-pause')?.addEventListener('click', async () => {
  try { await fetch('/api/farm/pause', { method: 'POST' }); notify('Automation pause state updated.'); } catch { notify('Could not reach the automation connector.'); }
});
let comboData = {};
// Use the catalog's tile order within each category, including new maps inserted at the front.
const normalizeMapName = BloonsMapNames.normalize;
const CATEGORY_ORDER = Object.keys(mapCatalog);
const categoryBySlug = {};
mapChoices.forEach(({ name, category }) => { categoryBySlug[normalizeMapName(name)] = category; });
function mergeDiscoveredMaps(learned) {
  for (const entry of Object.values(learned)) {
    if (!entry.discovered || !CATEGORY_ORDER.includes(entry.category) || !Number.isInteger(entry.page) || !Number.isInteger(entry.pos)) continue;
    const key = normalizeMapName(entry.name);
    if (!key || categoryBySlug[key]) continue;
    mapChoices.push({ name: entry.name, category: entry.category });
    categoryBySlug[key] = entry.category;
  }
  const position = map => {
    const category = CATEGORY_ORDER.indexOf(map.category);
    const learnedEntry = learned[normalizeMapName(map.name)];
    const catalogIndex = mapCatalog[map.category]?.findIndex(name => normalizeMapName(name) === normalizeMapName(map.name)) ?? -1;
    const withinCategory = learnedEntry && Number.isInteger(learnedEntry.page) && Number.isInteger(learnedEntry.pos)
      ? learnedEntry.page * 6 + learnedEntry.pos : catalogIndex >= 0 ? catalogIndex : 999;
    return category * 1000 + withinCategory;
  };
  mapChoices.sort((a, b) => position(a) - position(b) || a.name.localeCompare(b.name));
}
function categoryForMapSlug(mapSlug) { return categoryBySlug[normalizeMapName(mapSlug)] || 'Other'; }
const GAMEMODES_BY_DIFFICULTY = {
  easy: ['easy', 'primary_only', 'deflation'],
  medium: ['medium', 'military_only', 'reverse', 'apopalypse'],
  hard: ['hard', 'magic_monkeys_only', 'double_hp_moabs', 'half_cash', 'alternate_bloons_rounds', 'impoppable', 'chimps'],
};
function renderGamemodeOptions() {
  const mapSlug = document.querySelector('#playthrough-map-select').value;
  const select = document.querySelector('#playthrough-gamemode-select');
  const previous = select.value;
  select.replaceChildren();
  Object.entries(GAMEMODES_BY_DIFFICULTY).forEach(([difficulty, modes]) => {
    const option = document.createElement('option');
    option.value = difficulty;
    option.textContent = difficulty[0].toUpperCase() + difficulty.slice(1);
    option.disabled = !modes.some(mode => comboData[mapSlug]?.[mode]?.length);
    select.append(option);
  });
  if ([...select.options].some(option => option.value === previous)) select.value = previous;
  renderVariationOptions();
}
function renderVariationOptions() {
  const mapSlug = document.querySelector('#playthrough-map-select').value;
  const difficulty = document.querySelector('#playthrough-gamemode-select').value;
  const select = document.querySelector('#playthrough-variation-select');
  const previous = select.value;
  select.replaceChildren();
  (GAMEMODES_BY_DIFFICULTY[difficulty] || []).forEach(mode => {
    const option = document.createElement('option');
    option.value = mode;
    const available = !!comboData[mapSlug]?.[mode]?.length;
    const route = comboData[mapSlug]?.[mode]?.[0];
    const fallback = route?.reusedFromChimps
      ? ' · CHIMPS route reused'
      : route?.reusedFromHard
      ? ' · Hard route reused'
      : route?.onlineGuideSource
      ? (route.localWinVerified ? ' · guide route · won here' : route.sourceVerified ? ' · guide route · source win' : ' · guide route · source check needed')
      : route?.converted
      ? (route.verifiedForTarget ? ' · verified imported plan' : ' · imported plan · needs a confirmed win')
      : '';
    option.textContent = `${mode === difficulty ? 'Standard' : mode.replace(/_/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase())}${available ? fallback : ' · route needed'}`;
    option.disabled = !available;
    select.append(option);
  });
  if ([...select.options].some(option => option.value === previous)) select.value = previous;
  renderSpecificMapRequirements();
}
function syncSelectedRunButton() {
  const button = document.querySelector('#farm-file');
  if (!button) return;
  const map = document.querySelector('#playthrough-map-select')?.value;
  const mode = document.querySelector('#playthrough-variation-select')?.value;
  const status = latestAutomationStatus;
  button.disabled = !comboData[map]?.[mode]?.length || !status || status.statusUnavailable
    || status.statusStale || status.runtime?.available === false || status.running || !!status.busyWith
    || mapObservationFor(map)?.medals?.[mode] === true;
}
function renderSpecificMapRequirements() {
  const box = document.querySelector('#specific-map-requirements');
  if (!box) return;
  const map = document.querySelector('#playthrough-map-select')?.value || '';
  const mode = document.querySelector('#playthrough-variation-select')?.value || '';
  const route = comboData[map]?.[mode]?.[0];
  const observation = mapObservationFor(map);
  const medal = observation.medals?.[mode] === true;
  const medalKnown = Object.keys(observation.medals || {}).length > 0;
  const checks = [
    ['Route available', !!route, route ? (route.localWinVerified ? 'Verified route' : 'Recorded route') : 'No compatible route'],
    ['Map selected', !!map, map ? 'Ready' : 'Select a map'],
    ['Variation selected', !!mode, mode ? 'Ready' : 'Choose a variation'],
    ['Medal state read', medalKnown, !medalKnown ? 'Waiting for game save' : medal ? 'Already completed' : 'Not completed'],
  ];
  const rows = checks.map(([label, ok, detail]) => { const row=document.createElement('div'); row.className='requirement-item'; const mark=document.createElement('i'); mark.className=`requirement-mark ${ok?'valid':'invalid'}`; mark.textContent=ok?'✓':'×'; const span=document.createElement('span'); span.textContent=label; const b=document.createElement('b'); b.textContent=detail; row.append(mark,span,b); return row; });
  if (map) {
    const mechanic = window.BLOONS_MAP_MECHANICS?.getMapMechanics(map);
    if (mechanic && mechanic.status !== 'standard-visual-check') {
      const row = document.createElement('div'); row.className = 'requirement-item map-mechanic-heading';
      const mark = document.createElement('i'); mark.className = 'requirement-mark pending'; mark.textContent = '↻';
      const label = document.createElement('span'); label.textContent = `Map mechanic · ${mechanic.type.replace(/-/g, ' ')}`;
      const detail = document.createElement('b'); detail.textContent = mechanic.cycle;
      row.append(mark, label, detail); rows.push(row);
      for (const rule of mechanic.rules) {
        const ruleRow = document.createElement('div'); ruleRow.className = 'requirement-item map-mechanic-rule';
        const ruleMark = document.createElement('i'); ruleMark.className = 'requirement-mark pending'; ruleMark.textContent = '•';
        const ruleLabel = document.createElement('span'); ruleLabel.textContent = 'Route rule';
        const ruleDetail = document.createElement('b'); ruleDetail.textContent = rule;
        ruleRow.append(ruleMark, ruleLabel, ruleDetail); rows.push(ruleRow);
      }
      for (const advantage of mechanic.advantages || []) {
        const advantageRow = document.createElement('div'); advantageRow.className = 'requirement-item map-mechanic-rule';
        const advantageMark = document.createElement('i'); advantageMark.className = 'requirement-mark valid'; advantageMark.textContent = '＋';
        const advantageLabel = document.createElement('span'); advantageLabel.textContent = 'Map opportunity';
        const advantageDetail = document.createElement('b'); advantageDetail.textContent = advantage;
        advantageRow.append(advantageMark, advantageLabel, advantageDetail); rows.push(advantageRow);
      }
    }
  }
  box.replaceChildren(...rows);
  syncSelectedRunButton();
  renderTowerRequirements();
}
const titleCase = slug => slug.split('_').map(word => word[0].toUpperCase() + word.slice(1)).join(' ');
function renderProfileUnlocks() {
  const status = document.querySelector('#profile-unlock-status');
  if (!status) return;
  const profile = detectedProgress.localProfile;
  if (!profile?.available) { status.textContent = 'Waiting for read-only Profile.Save data.'; return; }
  const heroes = profile.heroes?.unlocked || [];
  const knowledge = profile.monkeyKnowledge;
  const knowledgeSummary = BloonsKnowledge.summarize(knowledge);
  const mkState = {enabled:'enabled', disabled:'disabled', partial:'partly enabled', unknown:'state unavailable'}[knowledgeSummary.state];
  const bonusState = knowledge?.bonusMonkey === true ? 'Bonus Monkey unlocked' : knowledge?.bonusMonkey === false ? 'Bonus Monkey not unlocked' : 'Bonus Monkey unknown';
  const glueState = knowledge?.bonusGlueGunner === true ? 'Bonus Glue Gunner unlocked' : knowledge?.bonusGlueGunner === false ? 'Bonus Glue Gunner not unlocked' : 'Bonus Glue Gunner unknown';
  status.textContent = `${heroes.length} heroes unlocked${heroes.length ? ` · ${heroes.join(', ')}` : ''} · Monkey Knowledge ${mkState} · ${bonusState} · ${glueState}`;
  const knowledgeStatus = document.querySelector('#profile-monkey-knowledge');
  if (knowledgeStatus) {
    const spent = Array.isArray(knowledge?.paidFor) ? knowledge.paidFor : knowledge?.acquired || [];
    const prettyName = id => String(id).replace(/([a-z0-9])([A-Z])/g, '$1 $2').replace(/[_-]+/g, ' ');
    const points = Number.isFinite(knowledge?.pointsAvailable) ? `${knowledge.pointsAvailable} point${knowledge.pointsAvailable === 1 ? '' : 's'} available` : 'points unavailable';
    knowledgeStatus.replaceChildren();
    const summary = document.createElement('small');
    summary.textContent = `${mkState} · ${spent.length} purchased node${spent.length === 1 ? '' : 's'} · ${points}`;
    knowledgeStatus.append(summary);
    if (spent.length) {
      const details = document.createElement('details');
      const caption = document.createElement('summary'); caption.textContent = 'View purchased knowledge';
      const list = document.createElement('ul');
      for (const entry of spent) {
        const id = typeof entry === 'string' ? entry : entry?.id || entry?.name || '';
        const active = BloonsKnowledge.activity(knowledge, id);
        const item = document.createElement('li');
        item.textContent = `${prettyName(id)} — ${active === true ? 'active' : active === false ? 'inactive' : 'active state unknown'}`;
        list.append(item);
      }
      details.append(caption, list); knowledgeStatus.append(details);
    }
    knowledgeStatus.title = 'Read from Profile.Save. Bloons+ does not change Monkey Knowledge or game files.';
  }
}
// Only what the selected route uses: its hero, and each tower's highest tier per path.
function renderTowerRequirements() {
  const list = document.querySelector('#specific-tower-requirements'); if (!list) return;
  const map = document.querySelector('#playthrough-map-select')?.value || '';
  const mode = document.querySelector('#playthrough-variation-select')?.value || '';
  const needs = comboData[map]?.[mode]?.[0]?.requirements;
  if (!needs) {
    const empty = document.createElement('p'); empty.className = 'muted'; empty.textContent = 'Select a map and variation with a route to see what it needs.';
    list.replaceChildren(empty); return;
  }
  const observed = detectedProgress?.towers || {};
  const ownedUpgrades = unlockedUpgradeSet();
  const cards = [];
  if (needs.hero) {
    const unlockedHeroes = detectedProgress.heroes?.unlocked;
    const enabled = Array.isArray(unlockedHeroes) && unlockedHeroes.some(hero => mapProgressKey(hero) === mapProgressKey(needs.hero));
    const row = document.createElement('div'); row.className = 'tower-requirement-card';
    const title = document.createElement('div'); title.className = 'tower-requirement-title';
    const name = document.createElement('b'); name.textContent = `Hero: ${titleCase(needs.hero)}`;
    const note = document.createElement('small'); note.textContent = enabled ? 'Unlocked in game save' : Array.isArray(unlockedHeroes) ? 'Not unlocked in game save' : 'Waiting for hero data';
    title.append(name, note);
    const pills = document.createElement('div'); pills.className = 'tier-pills';
    const pill = document.createElement('span'); pill.className = `tier-pill ${enabled ? 'valid' : 'invalid'}`; pill.textContent = enabled ? '✓ Hero' : '× Hero';
    pills.append(pill); row.append(title, pills); cards.push(row);
  }
  for (const id of needs.knowledge || []) {
    const mk = detectedProgress.localProfile?.monkeyKnowledge || {};
    const active = BloonsKnowledge.activity(mk, id);
    const ready = active === true;
    const unknown = active === null;
    const row = document.createElement('div'); row.className = 'tower-requirement-card';
    const title = document.createElement('div'); title.className = 'tower-requirement-title';
    const name = document.createElement('b'); name.textContent = id === 'MasterDoubleCross' ? 'Master Double Cross' : id;
    const note = document.createElement('small');
    note.textContent = ready ? 'Acquired and active' : mk.enabled === false ? 'Monkey Knowledge is disabled' : unknown ? 'Waiting for knowledge data' : 'Not acquired or individually disabled';
    const pill = document.createElement('span'); pill.className = `tier-pill ${ready ? 'valid' : unknown ? 'unknown' : 'invalid'}`;
    pill.textContent = `${ready ? '✓' : unknown ? '?' : '×'} Required knowledge`;
    title.append(name, note); row.append(title, pill); cards.push(row);
  }
  for (const [slug, tiers] of Object.entries(needs.towers || {})) {
    const display = TOWER_NAMES[slug] || titleCase(slug);
    const tower = observed[display] || {};
    const row = document.createElement('div'); row.className = 'tower-requirement-card';
    const title = document.createElement('div'); title.className = 'tower-requirement-title';
    const name = document.createElement('b'); name.textContent = display;
    const note = document.createElement('small'); note.textContent = `Required path tiers · ${tiers.join(' / ')}`;
    title.append(towerThumb(display), name, note);
    const paths = document.createElement('div'); paths.className = 'requirement-paths';
    for (let pathIndex = 0; pathIndex < 3; pathIndex++) {
      const requiredTier = Number(tiers[pathIndex]) || 0;
      if (!requiredTier) continue;
      const pathRow = document.createElement('div'); pathRow.className = 'requirement-path-row';
      const pathLabel = document.createElement('b'); pathLabel.textContent = `Path ${pathIndex + 1}`; pathRow.append(pathLabel);
      for (let tier = 1; tier <= requiredTier; tier++) {
        const upgradeName = upgradeNameFor(display, pathIndex, tier);
        const unlocked = ownsUpgrade(ownedUpgrades, display, upgradeName);
        const known = upgradeTierKnown(upgradeName, Array.isArray(detectedProgress.localProfile?.acquiredUpgrades));
        const pill = document.createElement('span');
        pill.className = `tier-pill ${unlocked ? 'valid' : known ? 'invalid' : 'unknown'} ${tier <= requiredTier ? 'route-required' : ''}`;
        pill.textContent = `${unlocked ? '✓' : known ? '×' : '?'} T${tier}`;
        pill.title = `${upgradeName || `Tier ${tier}`} · ${unlocked ? 'unlocked in save' : known ? 'not unlocked' : 'status unknown'}${tier <= requiredTier ? ' · required by this route' : ''}`;
        pathRow.append(pill);
      }
      paths.append(pathRow);
    }
    row.append(title, paths); cards.push(row);
  }
  list.replaceChildren(...cards);
}
async function loadPlaythroughs() {
  try {
    const [response, orderResponse] = await Promise.all([
      fetch('/api/playthrough-combos', { cache: 'no-store', signal: AbortSignal.timeout(30000) }),
      fetch('/api/map-order', { cache: 'no-store' }),
    ]);
    if (!response.ok) return;
    comboData = await response.json();
    const learned = orderResponse.ok ? (await orderResponse.json()).maps || {} : {};
    mergeDiscoveredMaps(learned);
    const mapSelect = document.querySelector('#playthrough-map-select'); mapSelect.replaceChildren();
    const groups = {};
    const catalogOrder = new Map(mapChoices.map(({ name }, index) => [normalizeMapName(name), index]));
    const tileOrder = slug => {
      const entry = learned[normalizeMapName(slug)];
      if (entry && Number.isInteger(entry.page) && Number.isInteger(entry.pos)) {
        const category = CATEGORY_ORDER.indexOf(entry.category);
        if (category >= 0) return category * 1000 + entry.page * 6 + entry.pos;
      }
      return catalogOrder.get(normalizeMapName(slug)) ?? Infinity;
    };
    const catalogSlugs = new Map(Object.keys(comboData).map(slug => [normalizeMapName(slug), slug]));
    const allSlugs = new Set([...Object.keys(comboData), ...mapChoices.map(map => catalogSlugs.get(normalizeMapName(map.name)) || map.name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, ''))]);
    [...allSlugs].sort((a, b) => tileOrder(a) - tileOrder(b) || a.localeCompare(b)).forEach(mapSlug => {
      const category = categoryForMapSlug(mapSlug);
      (groups[category] ||= []).push(mapSlug);
    });
    [...CATEGORY_ORDER, 'Other'].forEach(category => {
      if (!groups[category]?.length) return;
      const optgroup = document.createElement('optgroup'); optgroup.label = category;
      groups[category].forEach(mapSlug => {
        const option = document.createElement('option'); option.value = mapSlug;
        const routeAvailable = Object.keys(comboData[mapSlug] || {}).length > 0;
        option.textContent = `${mapChoices.find(map => normalizeMapName(map.name) === normalizeMapName(mapSlug))?.name || mapSlug.replace(/_/g, ' ')}${routeAvailable ? '' : ' · route needed'}`;
        option.disabled = !routeAvailable;
        optgroup.append(option);
      });
      mapSelect.append(optgroup);
    });
    renderGamemodeOptions();
  } catch { /* AutoBTD6 not vendored/set up yet */ }
}
document.querySelector('#playthrough-map-select').addEventListener('change', renderGamemodeOptions);
document.querySelector('#playthrough-gamemode-select').addEventListener('change', renderVariationOptions);
loadPlaythroughs();
// Heroes are read-only from the local Profile.Save reader; there is no manual hero setting.
loadAutomationStatus();
setInterval(() => { if (!document.hidden) loadAutomationStatus(); }, 750);
document.addEventListener('visibilitychange', () => { if (!document.hidden) loadAutomationStatus(); });
window.addEventListener('focus', loadAutomationStatus);


document.querySelector('a[href="/calibrate.html"]')?.addEventListener('click', event => {
  event.preventDefault();
  let dialog = document.querySelector('#calibration-dialog');
  if (!dialog) {
    dialog = document.createElement('dialog'); dialog.id = 'calibration-dialog';
    dialog.style.cssText = 'max-width:min(1400px,96vw);width:96vw;height:90vh;padding:0;overflow:hidden;border-radius:28px';
    dialog.innerHTML = '<div style="display:flex;justify-content:flex-end;padding:10px;background:#ffffffaa"><button class="quiet-button" type="button">Close</button></div><iframe src="/calibrate.html" title="Scanner calibration" style="border:0;width:100%;height:calc(100% - 52px)"></iframe>';
    dialog.querySelector('button').addEventListener('click', () => dialog.close());
    document.body.append(dialog);
  }
  dialog.showModal();
});



// Reports include only a reviewed, redacted excerpt; no private profile files.
const reportDialog = document.querySelector('#issue-report-dialog');
function updateIssueReport() {
  const excerpt = window.BloonsSupport.redact(latestRunLog || 'No run log available.').slice(-4500);
  document.querySelector('#report-preview').textContent = excerpt;
  const description = window.BloonsSupport.redact(document.querySelector('#report-description').value).slice(0,1500);
  const body = `## What happened\n${description || 'Describe what happened here.'}\n\n## Run context\nApp: Bloons+ 0.1.0\nEngine: ${latestAutomationStatus?.vm ? 'VM' : 'Local / unknown'}\n\n## Redacted log excerpt\n\`\`\`text\n${excerpt.replace(/\`/g, "'")}\n\`\`\`\n`;
  document.querySelector('#report-submit').href = 'https://github.com/Klaasawastaken/BloonsPlus/issues/new?title=' + encodeURIComponent('Run issue') + '&body=' + encodeURIComponent(body);
}
document.querySelectorAll('#report-issue, #settings-report-issue').forEach(button => button.addEventListener('click', () => { updateIssueReport(); reportDialog.showModal(); }));
document.querySelector('#report-close').addEventListener('click', () => reportDialog.close());
document.querySelector('#report-description').addEventListener('input', updateIssueReport);
document.querySelector('#report-download').addEventListener('click', () => {
  const blob = new Blob([window.BloonsSupport.redact(latestRunLog || 'No run log available.')], { type: 'text/plain' });
  const href = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = href; a.download = 'bloonsplus-redacted-log.txt'; a.click(); setTimeout(() => URL.revokeObjectURL(href), 1000);
});
