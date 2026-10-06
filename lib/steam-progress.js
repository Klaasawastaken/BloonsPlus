// Reads BTD6's achievement progress from Steam's own local cache instead of OCR-scanning the
// achievements screen. Steam already keeps two small files per installed game:
//   appcache/stats/UserGameStatsSchema_<appid>.bin  - every achievement's name/description/hidden
//                                                      flag and (for counter achievements) which
//                                                      stat it tracks and its target value.
//   appcache/stats/UserGameStats_<steam3id>_<appid>.bin - this account's unlocked bits, unlock
//                                                          times, and the live value of every stat.
// Both are Valve's binary VDF format (a tiny nested key/value tree) and are written locally by the
// Steam client itself; nothing here touches BTD6's own files or process. The <steam3id> in the
// second filename identifies an account, but several accounts can be cached. Resolve the
// active account before reading it. Ninja Kiwi's temporary player-cache files are not used.
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const {readActiveSteamAccount,selectSteamAccount} = require('./steam-account');

const APP_ID = '960090';

function readBinaryVDF(buffer) {
  let offset = 0;
  const requireBytes = count => {
    if (offset + count > buffer.length) throw new Error('Steam cache is truncated');
  };
  const readCString = () => {
    const start = offset;
    while (offset < buffer.length && buffer[offset] !== 0) offset++;
    if (offset >= buffer.length) throw new Error('Steam cache contains an unterminated string');
    const value = buffer.toString('utf8', start, offset);
    offset++;
    return value;
  };
  const readObject = () => {
    const object = {};
    for (;;) {
      requireBytes(1);
      const type = buffer[offset]; offset++;
      if (type === 0x08) return object; // end of this object
      const key = readCString();
      if (type === 0x00) object[key] = readObject();
      else if (type === 0x01) object[key] = readCString();
      else if (type === 0x02) { requireBytes(4); object[key] = buffer.readInt32LE(offset); offset += 4; }
      else if (type === 0x03) { requireBytes(4); object[key] = buffer.readFloatLE(offset); offset += 4; }
      else if (type === 0x06 || type === 0x07) { requireBytes(8); object[key] = Number(buffer.readBigUInt64LE(offset)); offset += 8; }
      else throw new Error(`unknown binary VDF field type ${type}`);
    }
  };
  return readObject();
}

function findSteamPath() {
  if (process.env.STEAM_PATH && fs.existsSync(process.env.STEAM_PATH)) return process.env.STEAM_PATH;
  try {
    const output = execFileSync('reg', ['query', 'HKCU\\Software\\Valve\\Steam', '/v', 'SteamPath'],
      { windowsHide: true, timeout: 5000, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    const match = output.match(/SteamPath\s+REG_SZ\s+(.+)/i);
    if (match) return match[1].trim().replace(/\//g, path.sep);
  } catch { /* registry lookup unavailable; fall through to common paths */ }
  return ['C:\\Program Files (x86)\\Steam', 'C:\\Program Files\\Steam'].find(candidate => fs.existsSync(candidate)) || null;
}

// An active account wins; without that signal only a single cached account is unambiguous.
function findStatsFile(steamPath, account) {
  const dir = path.join(steamPath, 'appcache', 'stats');
  let entries;
  try { entries = fs.readdirSync(dir); } catch { return null; }
  const candidates = entries.map(name => ({name,id:name.match(/^UserGameStats_(\d+)_960090\.bin$/)?.[1]})).filter(entry => entry.id);
  const selected = selectSteamAccount(candidates.map(entry => entry.id),account);
  const match = candidates.find(entry => entry.id === selected)?.name;
  return match ? path.join(dir, match) : null;
}

let cache = null;
// Achievements rarely change and this reads two small local files, so a short cache is enough to
// avoid re-parsing on every poll without ever showing stale data for more than a few seconds.
const CACHE_MS = 15_000;

function readSteamAchievements() {
  const account = readActiveSteamAccount();
  const accountKey = account.state + ':' + (account.id || '');
  if (cache && cache.accountKey === accountKey && Date.now() - cache.readAt < CACHE_MS) return cache.result;
  const result = computeSteamAchievements(account);
  cache = { readAt: Date.now(), accountKey, result };
  return result;
}

function computeSteamAchievements(account) {
  const steamPath = findSteamPath();
  if (!steamPath) return { available: false, reason: 'Steam installation not found' };
  const schemaPath = path.join(steamPath, 'appcache', 'stats', `UserGameStatsSchema_${APP_ID}.bin`);
  const statsPath = findStatsFile(steamPath,account);
  if (!fs.existsSync(schemaPath) || !statsPath) {
    return { available: false, reason: 'Active BTD6 achievement cache unavailable or cached accounts are ambiguous; open Steam with the BTD6 account' };
  }
  let schema, stats;
  try {
    schema = readBinaryVDF(fs.readFileSync(schemaPath));
    stats = readBinaryVDF(fs.readFileSync(statsPath));
  } catch (error) {
    return { available: false, reason: `could not read Steam's achievement cache: ${error.message}` };
  }
  const groups = schema[Object.keys(schema)[0]]?.stats || {};
  const cacheData = stats.cache || {};

  // A group with `bits` holds achievement definitions; a group without holds a plain named counter
  // (e.g. "bloonsPopped") that a counter-achievement's `progress.value.operand1` refers to by name.
  const statByName = {};
  for (const [groupId, group] of Object.entries(groups)) {
    if (!group.bits && group.name && cacheData[groupId] && typeof cacheData[groupId].data === 'number') {
      statByName[group.name] = cacheData[groupId].data;
    }
  }

  const achievements = [];
  for (const [groupId, group] of Object.entries(groups)) {
    if (!group.bits) continue;
    const unlockTimes = cacheData[groupId]?.AchievementTimes || {};
    for (const [bit, definition] of Object.entries(group.bits)) {
      const name = definition.display?.name?.english;
      if (!name) continue;
      const unlockedAt = unlockTimes[bit];
      const progressDef = definition.progress;
      let progress = null;
      if (progressDef?.value?.operand1 && progressDef.value.operand1 in statByName) {
        progress = { current: Math.min(statByName[progressDef.value.operand1], progressDef.max_val ?? Infinity),
          target: progressDef.max_val ?? null };
      }
      achievements.push({
        name,
        description: definition.display?.desc?.english || null,
        hidden: definition.display?.hidden === 1 || definition.display?.hidden === '1',
        unlocked: unlockedAt != null,
        unlockedAt: unlockedAt != null ? new Date(unlockedAt * 1000).toISOString() : null,
        progress,
      });
    }
  }
  return { available: true, source: 'steam-local', readAt: new Date().toISOString(), achievements };
}

module.exports = { readSteamAchievements };
