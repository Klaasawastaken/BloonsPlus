// Read-only decoder for Steam's BTD6 Profile.Save.
// Format: 44-byte header, 24-byte salt at 52, AES-128-CBC payload at 76,
// PBKDF2-SHA1(password "11", 10 rounds) and zlib-compressed JSON.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const { execFileSync } = require('node:child_process');
const {readActiveSteamAccount,selectSteamAccount} = require('./steam-account');

const APP_ID = '960090';
const { medalsFromMapRecord } = require('../data/catalogs/medal-progress');
function steamRoots() {
  const roots = [];
  if (process.env.STEAM_PATH) roots.push(process.env.STEAM_PATH);
  try {
    const out = execFileSync('reg', ['query', 'HKCU\\Software\\Valve\\Steam', '/v', 'SteamPath'],
      { windowsHide: true, timeout: 5000, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    const match = out.match(/SteamPath\s+REG_SZ\s+(.+)/i);
    if (match) roots.push(match[1].trim().replace(/\//g, path.sep));
  } catch { /* registry is optional */ }
  roots.push('C:\\Program Files (x86)\\Steam', 'C:\\Program Files\\Steam');
  return [...new Set(roots)].filter(fs.existsSync);
}
function findProfileSave() {
  const profiles = [];
  for (const root of steamRoots()) {
    const base = path.join(root, 'userdata');
    let users = [];
    try { users = fs.readdirSync(base, { withFileTypes: true }).filter(e => e.isDirectory()).map(e => e.name); } catch { continue; }
    for (const user of users) {
      const direct = path.join(base, user, APP_ID, 'local');
      const candidates = [path.join(direct, 'Profile.Save'), path.join(direct, 'link', 'PRODUCTION', 'current', 'Profile.Save')];
      let found = candidates.find(file => fs.existsSync(file));
      // Steam may use a generated link directory rather than current.
      for (const parent of found ? [] : [path.join(direct, 'link'), path.join(direct, 'link', 'PRODUCTION')]) {
        try {
          for (const entry of fs.readdirSync(parent, { withFileTypes: true })) {
            if (!entry.isDirectory()) continue;
            const file = path.join(parent, entry.name, 'Profile.Save');
            if (fs.existsSync(file)) { found = file; break; }
          }
        } catch { /* directory is optional */ }
        if (found) break;
      }
      if (found && /^\d+$/.test(user)) profiles.push({account:user,file:found});
    }
  }
  const selected = selectSteamAccount(profiles.map(profile => profile.account),readActiveSteamAccount());
  return profiles.find(profile => profile.account === selected)?.file || null;
}
function decodeProfileSave(file) {
  const data = fs.readFileSync(file);
  if (data.length < 92) throw new Error('invalid Profile.Save length');
  // Version 1 uses salt/payload offsets 52/76. Newer saves add a variable-length
  // account identifier to the header. Try the documented offset first, then locate
  // the unique salt/payload boundary by requiring successful AES + zlib decoding.
  const starts = [52, ...Array.from({ length: 61 }, (_, i) => 27 + i)];
  for (const saltStart of [...new Set(starts)]) {
    const encryptedStart = saltStart + 24;
    if (encryptedStart >= data.length || (data.length - encryptedStart) % 16) continue;
    try {
      const salt = data.subarray(saltStart, encryptedStart);
      const derived = crypto.pbkdf2Sync(Buffer.from('11'), salt, 10, 32, 'sha1');
      const decipher = crypto.createDecipheriv('aes-128-cbc', derived.subarray(16, 32), derived.subarray(0, 16));
      const decrypted = Buffer.concat([decipher.update(data.subarray(encryptedStart)), decipher.final()]);
      return JSON.parse(zlib.inflateSync(decrypted).toString('utf8').replace(/^\uFEFF/, ''));
    } catch { /* candidate boundary was not the save's encrypted payload */ }
  }
  throw new Error('unsupported or corrupt Profile.Save format');
}
function findKey(value, names, seen = new Set()) {
  if (!value || typeof value !== 'object' || seen.has(value)) return null;
  seen.add(value);
  for (const [key, child] of Object.entries(value)) {
    if (names.has(key.toLowerCase())) return child;
    const found = findKey(child, names, seen);
    if (found != null) return found;
  }
  return null;
}
// Every BTD6 binding the automation presses. Unbound ones make routes skip steps, so the app
// lists them with a free key to bind (read-only: the save itself is never written).
const REQUIRED_HOTKEYS = [
  ...['Heroes', 'DartMonkey', 'BoomerangMonkey', 'BombShooter', 'TackShooter', 'IceMonkey', 'GlueGunner', 'Desperado',
    'SniperMonkey', 'MonkeySub', 'MonkeyBuccaneer', 'MonkeyAce', 'HeliPilot', 'MortarMonkey', 'DartlingGunner',
    'WizardMonkey', 'SuperMonkey', 'NinjaMonkey', 'Alchemist', 'Druid', 'Mermonkey', 'BananaFarm', 'SpikeFactory',
    'MonkeyVillage', 'EngineerMonkey', 'BeastHandler', 'Skywarden', 'Upgrade Path 1', 'Upgrade Path 2',
    'Upgrade Path 3', 'ChangeTargeting', 'TowerSpecial'].map(name => ['monkeys', name]),
  ...['Sell', 'PlayFastForward', ...Array.from({ length: 10 }, (_, i) => `Activated Ability ${i + 1}`)].map(name => ['gameplay', name]),
];
const FREE_KEY_PREFERENCE = ['Backspace', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
  'Delete', 'Insert', 'Home', 'End', 'Numpad1', 'Numpad2', 'Numpad3', 'Numpad4', 'Numpad5', 'Numpad6', 'Numpad7',
  'Numpad8', 'Numpad9', 'Comma', 'Period', 'Backslash', 'P', 'J', 'K', 'E', 'R'];
function hotkeyReport(hotkeys) {
  if (!hotkeys || (!hotkeys.monkeys && !hotkeys.gameplay)) return null;
  const used = new Set();
  for (const section of Object.values(hotkeys)) for (const bind of Object.values(section || {})) {
    if (bind?.path && !bind.modifierKey) used.add(bind.path.split('/').pop().toLowerCase());
  }
  const missing = [];
  for (const [section, name] of REQUIRED_HOTKEYS) {
    if (hotkeys[section]?.[name]?.path) continue;
    const recommended = FREE_KEY_PREFERENCE.find(key => !used.has(key.toLowerCase())) || null;
    if (recommended) used.add(recommended.toLowerCase());
    missing.push({ action: name.replace(/([a-z])([A-Z])/g, '$1 $2'), recommended });
  }
  return { total: REQUIRED_HOTKEYS.length, bound: REQUIRED_HOTKEYS.length - missing.length, missing };
}

function readLocalProgress() {
  const file = findProfileSave();
  if (!file) return { available: false, reason: 'Active Steam Profile.Save unavailable or cached accounts are ambiguous; open Steam with the BTD6 account' };
  try {
    const save = decodeProfileSave(file);
    const towerXp = findKey(save, new Set(['towerxp'])) || {};
    const unlockedHeroes = Array.isArray(save.unlockedHeroes) ? save.unlockedHeroes : [];
    const acquiredKnowledge = findKey(save, new Set(['acquiredknowledge', 'unlockedknowledge', 'monkeyknowledgeunlocked'])) || [];
    const paidForKnowledge = Array.isArray(save.paidForKnowledge) ? save.paidForKnowledge : acquiredKnowledge;
    const knowledgeEnabled = typeof save.knowledgeDisabled === 'boolean' ? !save.knowledgeDisabled
      : typeof save.isKnowledgeEnabled === 'boolean' ? save.isKnowledgeEnabled
        : findKey(save, new Set(['isknowledgeenabled', 'monkeyknowledgeenabled']));
    const knowledgeIds = Array.isArray(acquiredKnowledge) ? acquiredKnowledge
      : Object.entries(acquiredKnowledge || {}).filter(([, owned]) => owned === true).map(([id]) => id);
    const normalizedKnowledge = knowledgeIds.map(value => String(value?.id || value?.name || value).toLowerCase().replace(/[^a-z0-9]/g, ''));
    const hasBonusMonkey = normalizedKnowledge.some(id => id === 'bonusmonkey' || id === 'bonusmonkeyknowledge');
    const hasBonusGlueGunner = normalizedKnowledge.some(id => id === 'bonusgluegunner' || id === 'bonusgluegunnerknowledge');
    // Current saves place map medals under mapInfo.maps; older builds used a flatter
    // mapProgress/mapMedals field, so retain both layouts when present.
    const mapProgress = save.mapInfo?.maps || findKey(save, new Set(['mapmedals', 'mapprogress', 'mapmedal'])) || {};
    return {
      available: true, source: 'btd6-profile-save', file, readAt: new Date().toISOString(),
      towerXp, mapProgress, rank: save.rank, xp: save.xp, veteranXp: save.veteranXp,
      veteranRank: save.veteranRank, monkeyMoney: save.monkeyMoney,
      heroes: { unlocked: unlockedHeroes, primary: save.primaryHero || null },
      // BTD6's own tower hotkeys; an empty path means the tower has no hotkey bound.
      gameHotkeys: { monkeys: save.hotkeysData2?.monkeys || {}, gameplay: save.hotkeysData2?.gameplay || {} },
      hotkeyReport: hotkeyReport(save.hotkeysData2),
      towerHotkeys: Object.fromEntries(Object.entries(save.hotkeysData2?.monkeys || {}).map(([name, bind]) => [name, bind?.path || ''])),
      monkeyKnowledge: {
        acquired: knowledgeIds,
        paidFor: Array.isArray(paidForKnowledge) ? paidForKnowledge : [],
        enabled: typeof knowledgeEnabled === 'boolean' ? knowledgeEnabled : null,
        pointsAvailable: Number.isFinite(save.knowledgePoints) ? save.knowledgePoints : null,
        bonusMonkey: hasBonusMonkey,
        bonusGlueGunner: hasBonusGlueGunner,
      },
      acquiredUpgrades: Array.isArray(save.acquiredUpgrades) ? save.acquiredUpgrades : [],
      viewedUpgrades: Array.isArray(save.viewedUpgrades) ? save.viewedUpgrades : [],
      towerUnlockProgresses: save.towerUnlockProgresses && typeof save.towerUnlockProgresses === 'object' ? save.towerUnlockProgresses : {},
      paragonUpgradesPurchased: Array.isArray(save.paragonUpgradesPurchased) ? save.paragonUpgradesPurchased : [],
      unlockedTowers: Array.isArray(save.unlockedTowers) ? save.unlockedTowers : [],
      // Boss badges are event-level counters in Profile.Save; they are not tied to a specific
      // boss name, so the UI must never present them as per-boss Normal/Elite clears.
      bossMedals: save.bossMedals && typeof save.bossMedals === 'object' ? save.bossMedals : {},
    };
  } catch (error) {
    return { available: false, source: 'btd6-profile-save', reason: `could not read Profile.Save: ${error.message}` };
  }
}
module.exports = { readLocalProgress, findProfileSave, decodeProfileSave, medalsFromMapRecord };
