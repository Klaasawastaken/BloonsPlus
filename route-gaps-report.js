// Writes route-gaps.json: every map/mode pair still without a usable route (per route-coverage.json),
// annotated with what was searched and why it could not be filled, plus every candidate source file
// import-public-routes.py rejected (from route-library/metadata/public-route-import.json). Run this
// after route-coverage-report.js and import-public-routes.py. Usage: node route-gaps-report.js
const fs = require('node:fs');
const path = require('node:path');

const ROOT = __dirname;
const coverage = JSON.parse(fs.readFileSync(path.join(ROOT, 'route-coverage.json'), 'utf8'));
let importReport = { rejected: [] };
try { importReport = JSON.parse(fs.readFileSync(path.join(ROOT, 'route-library', 'metadata', 'public-route-import.json'), 'utf8')); } catch { /* not run yet */ }

const SOURCES_SEARCHED = [
  'GitHub code/repo search for BTD6 bots and macros (btd6+bot, btd6+macro, btd6+autoplay, bloonstd6+automation, btd6+chimps+bot)',
  'j-miet/BTD6bot (MIT) — plans/*.py, vendored in btd6bot/',
  'piweiblen/BloonsPlayer (MIT) — src/data/tas/*.txt, vendored in route-library/public-sources/piweiblen-BloonsPlayer',
  'ThuyTran735/BTD6-Everything-Macro (MIT) — Maps/**/*.ahk, vendored in route-library/public-sources/ThuyTran735-BTD6-Everything-Macro',
  'Randy-Hodges/BTD6-Autoplay (MIT) — Autoplay/action_scripts/collection_scripts/*.py, vendored in route-library/public-sources/Randy-Hodges-BTD6-Autoplay',
  'Griznah/btd6-auto (GPL-3.0) — btd6_auto/configs/maps/*.json: checked, almost every map file is a {"placeholder": true} stub with no coordinates',
  'machasins/btd6bot — data/map_scripts/**/*.json: repo returned empty tree via the GitHub API at the time of the search',
  'dawei7/BloonsTD6_BOT (MIT) — src/data/files/*.csv: only 2 maps (Tinkerton, In the Loop), both already covered',
  'linus-jansson/btd6farmer (MIT) — gameplans/*/instructions.json: only Dark Castle and Infernal, both already covered',
];

const rejectedByMap = {};
for (const r of importReport.rejected) {
  if (!r.map) continue;
  (rejectedByMap[r.map] ||= []).push(r);
}

const gaps = [];
for (const [slug, entry] of Object.entries(coverage.maps)) {
  for (const [mode, value] of Object.entries(entry.modes)) {
    if (Array.isArray(value)) continue; // covered
    const candidates = (rejectedByMap[slug] || []).filter(r => !r.mode || r.mode === mode);
    const drafts = value && value.draftsOnly ? value.draftsOnly : [];
    const gap = {
      map: slug, mapName: entry.name, category: entry.category, mode,
      searched: SOURCES_SEARCHED,
      rejectedCandidates: candidates.map(c => ({ source: c.source, sourceFile: c.sourceFile, reason: c.reason })),
      draftOnly: drafts,
      reason: candidates.length
        ? 'candidate strategy data exists in a searched source but could not be converted (see rejectedCandidates)'
        : drafts.length
          ? 'only a generated/draft adaptation exists; automation.js will not treat it as a verified route for this mode'
          : 'no candidate strategy with placement coordinates was found in any searched source for this map/mode',
    };
    gaps.push(gap);
  }
}

const summary = {
  generatedAt: new Date().toISOString(),
  totalGaps: gaps.length,
  gapsWithRejectedCandidate: gaps.filter(g => g.rejectedCandidates.length).length,
  gapsWithDraftOnly: gaps.filter(g => !g.rejectedCandidates.length && g.draftOnly.length).length,
  gapsWithNoCandidateFound: gaps.filter(g => !g.rejectedCandidates.length && !g.draftOnly.length).length,
  perMode: Object.fromEntries(coverage.modes.map(m => [m, gaps.filter(g => g.mode === m).length])),
  note: 'route-failures.json (runtime attempt failures) is written by the app itself and is not touched here.',
};

fs.writeFileSync(path.join(ROOT, 'route-gaps.json'), JSON.stringify({ summary, sourcesSearched: SOURCES_SEARCHED, gaps }, null, 2));
console.log(JSON.stringify(summary, null, 2));
