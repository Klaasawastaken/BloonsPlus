// Passive, read-only strategy telemetry. It never sends input to BTD6 or edits game saves.
const fs = require('node:fs');
const path = require('node:path');
const DATA_PATH = path.join(__dirname, 'experimental-ai-data.json');
const MAX_LEARNED_EVENTS = 30000;
const BTD6_KNOWLEDGE = {
  interaction: 'Use simulated mouse and keyboard only; never modify game files or memory.',
  monkeyKnowledge: 'Monkey Knowledge may make actions free; confirm placement by screen state, not cash delta alone.',
  heroes: 'Prefer valid land heroes; place water heroes only on water and verify the selected hero in-game.',
  obstacles: 'Map obstacles can move, freeze, rotate, or temporarily block placement; recheck before placement.',
  upgrades: 'Verify each upgrade tier changed after clicking; reopen and retry when it is not confirmed.',
  recovery: 'Pause safely on errors and choose a previously confirmed alternative before abandoning a route.',
  validation: 'Only repeated confirmed victories produce advisory candidates.'
  ,wiki: {
    mapTiers: 'Maps are Beginner, Intermediate, Advanced, and Expert; multi-lane paths, water, line of sight, and obstacles affect placement.',
    coreRules: 'Rounds increase in difficulty; MOAB-class bloons begin in later rounds. BADs resist slowdown, knockback, and instakill; Purples resist fire, plasma, and energy; Camo, Regrow, and Fortified properties change counter requirements.',
    modes: 'Easy, Medium, and Hard are separate difficulties. Standard, Primary Only, Military Only, Magic Monkeys Only, Deflation, Half Cash, Alternate Bloons Rounds, Impoppable, and CHIMPS impose different restrictions.',
    progression: 'Mode medals unlock progressively on each map; map category unlocks depend on prior map wins. Heroes, fifth-tier upgrades, and Paragons are progression systems.',
    events: 'Boss events, Odysseys, Quests, and other event modes can have rules that differ from normal rounds and may require dedicated routes.',
    source: 'Bloons Wiki reference snapshot; verify balance and map mechanics against the current game version before automation.'
  }
};
function read() {
  try {
    const data = JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));
    data.routes ||= []; data.placements ||= []; data.candidates ||= [];
    data.learning ||= { cursors: {}, events: [], runs: [] };
    data.learning.cursors ||= {}; data.learning.events ||= []; data.learning.runs ||= [];
    return data;
  } catch { return { routes: [], placements: [], candidates: [], learning: { cursors: {}, events: [], runs: [] } }; }
}
function write(data) {
  const temporary = `${DATA_PATH}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(data, null, 2));
  fs.renameSync(temporary, DATA_PATH);
  return data;
}
function normaliseAction(action) {
  if (!action || typeof action !== 'object') return null;
  const pos = Array.isArray(action.pos) ? action.pos.map(Number) : null;
  if (action.kind !== 'place' || !pos || pos.length !== 2 || pos.some(v => !Number.isFinite(v))) return null;
  return { type: String(action.type || 'tower'), name: String(action.name || action.type || 'tower'), pos, round: Number(action.round) || null, upgrade: action.upgrade || null };
}
function ingestRoute(route) {
  const data = read();
  const actions = (Array.isArray(route.actions) ? route.actions : []).map(normaliseAction).filter(Boolean);
  const entry = { id: String(route.id || `${route.map || 'unknown'}-${Date.now()}`), map: String(route.map || 'unknown'), mode: String(route.mode || 'unknown'), resolution: route.resolution || null, actions, source: String(route.source || 'local'), importedAt: new Date().toISOString() };
  data.routes = data.routes.filter(item => item.id !== entry.id); data.routes.push(entry);
  const placements = actions.map(action => ({ ...action, map: entry.map, mode: entry.mode, resolution: entry.resolution, routeId: entry.id }));
  data.placements = [...data.placements.filter(item => item.routeId !== entry.id), ...placements];
  // Candidate generation is bounded and traceable: no invented coordinates.
  data.candidates = data.routes.flatMap(item => item.actions.map(action => ({ ...action, map: item.map, mode: item.mode, routeId: item.id, confidence: item.source === 'verified' ? 'verified' : 'recorded' })));
  return write(data);
}
function ingestGameState(state) {
  if (!state || typeof state.runId !== 'string' || !Array.isArray(state.events)) return { ingested: 0 };
  const data = read();
  const learning = data.learning;
  const runId = state.runId;
  let cursor = Number(learning.cursors[runId]) || 0;
  let ingested = 0;
  for (let index = cursor; index < state.events.length; index++) {
    const event = state.events[index];
    // Only durable, confirmed in-game actions become examples; issued/ambiguous inputs stay out.
    if (!event || !event.confirmedAt || !['place', 'upgrade', 'sell', 'ability', 'retarget'].includes(event.type)) continue;
    learning.events.push({ id: `${runId}:${index}`, runId, map: state.map || null, mode: state.mode || state.difficulty || null,
      round: Number.isFinite(event.round) ? event.round : null, action: event.type, tower: event.towerType || event.tower || null,
      position: Array.isArray(event.position) ? event.position.map(Number) : null,
      path: Number.isInteger(event.path) ? event.path : null, tier: Number.isInteger(event.upgradeLevel) ? event.upgradeLevel : null,
      cost: Number.isFinite(event.cost) ? event.cost : null, cashBefore: Number.isFinite(event.cashBefore) ? event.cashBefore : null,
      cashAfter: Number.isFinite(event.cashAfter) ? event.cashAfter : null, confirmedAt: event.confirmedAt, evidence: 'confirmed-game-state' });
    ingested++;
  }
  learning.cursors[runId] = state.events.length;
  if (Array.isArray(state.observations)) {
    const last = state.observations.at(-1);
    const previousId = learning.lastObservationId;
    const observationId = last?.observedAt ? `${runId}:${last.observedAt}` : null;
    if (observationId && observationId !== previousId) {
      learning.events.push({ id: observationId, runId, map: state.map || null, mode: state.mode || state.difficulty || null,
        round: Number.isFinite(last.round) ? last.round : null, cash: Number.isFinite(last.cash) ? last.cash : null,
        screen: last.screen || null, observedAt: last.observedAt, evidence: 'passive-screen-observation' });
      learning.lastObservationId = observationId;
      ingested++;
    }
  }
  if (state.result === 'victory' || state.result === 'defeat') {
    const outcomeId = `${runId}:outcome`;
    if (!learning.runs.some(run => run.id === outcomeId)) {
      learning.runs.push({ id: outcomeId, runId, map: state.map || null, mode: state.mode || state.difficulty || null,
        result: state.result, round: Number.isFinite(state.round) ? state.round : null, hero: state.hero || null,
        observedAt: state.updatedAt || new Date().toISOString(), evidence: 'game-state-result' });
      ingested++;
    }
  }
  learning.events = learning.events.slice(-MAX_LEARNED_EVENTS);
  learning.runs = learning.runs.slice(-5000);
  if (Object.keys(learning.cursors).length > 2000) {
    const keep = Object.entries(learning.cursors).slice(-1000);
    learning.cursors = Object.fromEntries(keep);
  }
  if (ingested) { learning.updatedAt = new Date().toISOString(); write(data); }
  return { ingested };
}
function status() {
  const data = read();
  const outcomes = data.learning.runs.reduce((result, run) => {
    result[run.result] = (result[run.result] || 0) + 1;
    return result;
  }, {});
  return { enabled: true, controlAvailable: false, mode: 'passive-read-only', knowledge: BTD6_KNOWLEDGE, routeCount: data.routes.length,
    placementCount: data.placements.length, candidateCount: data.candidates.length,
    observedEventCount: data.learning.events.length, confirmedActionCount: data.learning.events.filter(event => event.evidence === 'confirmed-game-state').length,
    observedRunCount: data.learning.runs.length, victories: outcomes.victory || 0, defeats: outcomes.defeat || 0,
    lastLearnedAt: data.learning.updatedAt || null };
}
function suggest(context = {}) {
  const data = read();
  const map = String(context.map || '').toLowerCase();
  const mode = String(context.mode || '').toLowerCase();
  const wins = data.learning.runs.filter(run => run.result === 'victory'
    && (!map || String(run.map || '').toLowerCase() === map)
    && (!mode || String(run.mode || '').toLowerCase() === mode));
  if (wins.length < 3) return { available: false, reason: 'Need three confirmed victories for this map/mode before suggesting actions.', knowledge: BTD6_KNOWLEDGE };
  const runIds = new Set(wins.map(run => run.runId));
  const examples = data.learning.events.filter(event => runIds.has(event.runId) && event.action === 'place' && Array.isArray(event.position));
  const grouped = new Map();
  for (const event of examples) {
    const key = `${event.tower || 'tower'}:${event.position.join(',')}`;
    const item = grouped.get(key) || { tower: event.tower || 'tower', position: event.position, uses: 0, rounds: [] };
    item.uses++; if (event.round != null) item.rounds.push(event.round); grouped.set(key, item);
  }
  const actions = [...grouped.values()].filter(item => item.uses >= 3).map(item => ({ ...item,
    confidence: Math.min(0.99, 0.6 + item.uses / (wins.length * 4)), source: 'confirmed-victories' }));
  return { available: actions.length > 0, map: context.map || null, mode: context.mode || null, victories: wins.length, actions, knowledge: BTD6_KNOWLEDGE };
}
function recordDecision(decision = {}) {
  const data = read();
  data.learning.decisions ||= [];
  data.learning.decisions.push({ ...decision, recordedAt: new Date().toISOString() });
  data.learning.decisions = data.learning.decisions.slice(-5000);
  write(data);
  return { ok: true };
}
module.exports = { ingestRoute, ingestGameState, suggest, recordDecision, status };
