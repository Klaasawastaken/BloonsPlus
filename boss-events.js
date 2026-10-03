// Read-only public event data. No game files, account identifiers, or OAK token are used.
const https = require('node:https');

const API_ORIGIN = 'https://data.ninjakiwi.com';
const CACHE_MS = 3 * 60 * 1000;
const ERROR_CACHE_MS = 30 * 1000;
let cached = null;
let expiresAt = 0;
let pending = null;

function getJson(pathname) {
  return new Promise((resolve, reject) => {
    const request = https.get(`${API_ORIGIN}${pathname}`, { headers: { Accept: 'application/json' }, timeout: 8000 }, response => {
      if (response.statusCode !== 200) {
        response.resume();
        return reject(new Error(`Ninja Kiwi API returned ${response.statusCode}`));
      }
      let body = '';
      response.setEncoding('utf8');
      response.on('data', chunk => {
        body += chunk;
        if (body.length > 2_000_000) request.destroy(new Error('Boss event response exceeded size limit'));
      });
      response.on('end', () => {
        try {
          const result = JSON.parse(body);
          if (result?.success !== true) throw new Error(result?.error || 'Boss event response was unsuccessful');
          resolve(result.body);
        } catch (error) { reject(error); }
      });
      response.on('error', reject);
    });
    request.on('timeout', () => request.destroy(new Error('Boss event request timed out')));
    request.on('error', reject);
  });
}

function compactMetadata(body) {
  if (!body || typeof body !== 'object') return null;
  const towers = Array.isArray(body._towers) ? body._towers : [];
  const limited = towers.filter(tower => Number.isFinite(tower.max) && tower.max >= 0).map(tower => ({
    tower: String(tower.tower || ''), max: tower.max, isHero: tower.isHero === true,
    blockedTiers: [1, 2, 3].map(index => Math.max(0, Number(tower[`path${index}NumBlockedTiers`]) || 0)),
  }));
  const modifiers = body._bloonModifiers || {};
  return {
    map: String(body.map || ''), mapURL: String(body.mapURL || ''),
    difficulty: String(body.difficulty || ''), mode: String(body.mode || ''),
    startRound: Number(body.startRound), endRound: Number(body.endRound),
    startingCash: Number(body.startingCash), maxTowers: Number(body.maxTowers), maxParagons: Number(body.maxParagons),
    disableMK: body.disableMK === true, disableSelling: body.disableSelling === true,
    disablePowers: body.disablePowers === true, disableInstas: body.disableInstas === true,
    bossSpeed: Number(modifiers.bossSpeedMultiplier) || 1,
    bossHealth: Number(modifiers.healthMultipliers?.boss) || 1,
    limitedTowers: limited,
  };
}

async function readActiveBossEvent() {
  if (cached && Date.now() < expiresAt) return cached;
  if (pending) return pending;
  pending = (async () => {
    try {
      const list = await getJson('/btd6/bosses');
      if (!Array.isArray(list)) throw new Error('Boss event list has an unexpected shape');
      const now = Date.now();
      const active = list.filter(item => Number(item.start) <= now && Number(item.end) > now)
        .sort((a, b) => Number(b.start) - Number(a.start))[0];
      if (!active) {
        cached = { available: true, active: false, source: 'ninja-kiwi-open-data', readAt: new Date().toISOString() };
      } else {
        const id = String(active.id || '');
        if (!/^[a-zA-Z0-9_-]{1,90}$/.test(id)) throw new Error('Boss event ID was invalid');
        const [normal, elite] = await Promise.all([
          getJson(`/btd6/bosses/${id}/metadata/standard`).then(compactMetadata),
          getJson(`/btd6/bosses/${id}/metadata/elite`).then(compactMetadata),
        ]);
        cached = {
          available: true, active: true, source: 'ninja-kiwi-open-data', readAt: new Date().toISOString(),
          id, bossType: String(active.bossType || '').toLowerCase(), name: String(active.name || ''),
          start: Number(active.start), end: Number(active.end),
          metadata: { normal, elite },
        };
      }
      expiresAt = Date.now() + CACHE_MS;
      return cached;
    } catch (error) {
      cached = { available: false, active: false, source: 'ninja-kiwi-open-data', reason: error.message, readAt: new Date().toISOString() };
      expiresAt = Date.now() + ERROR_CACHE_MS;
      return cached;
    } finally { pending = null; }
  })();
  return pending;
}

module.exports = { readActiveBossEvent };
