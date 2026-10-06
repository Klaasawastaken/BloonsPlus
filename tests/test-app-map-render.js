const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/app/app.js', 'utf8');
const start = source.indexOf('let lastMapRenderKey');
const fallback = source.indexOf('function renderMaps()');
const render = source.slice(start < 0 ? fallback : start, source.indexOf('function findMap(', fallback));
let hidden = true, renders = 0, reads = 0;
const medalSlots = [['easy'], ['chimps']];
let medals = { easy: true, chimps: false };
const grid = { replaceChildren() { renders++; } };
const filters = { childElementCount: 1, querySelectorAll: () => [] };
const nodes = {
  '#blackborder': { classList: { contains: () => hidden } },
  '#maps-grid': grid, '#maps-filters': filters,
  '#maps-search': { value: '' }, '#maps-hide-done': { checked: false }, '#queue-count': {}
};
const element = () => ({ className: '', append() {}, addEventListener() {} });
const context = {
  document: { querySelector: selector => nodes[selector], createElement: element },
  mapsCategory: 'All', mapChoices: [{ name: 'Logs', category: 'Beginner' }],
  MEDAL_SLOTS: medalSlots,
  mapObservationFor: () => { reads++; return { medals }; },
  isMapDone: () => medalSlots.every(([mode]) => medals[mode]),
  mapThumb: element, medalIcon: element
};
vm.createContext(context);
vm.runInContext(render, context);
const run = () => vm.runInContext('renderMaps()', context);
run();
assert.equal(reads, 0, 'Hidden maps must not construct card data');
assert.equal(renders, 0);
hidden = false;
run();
assert.equal(renders, 1, 'Showing Maps must render current data');
run();
assert.equal(renders, 1, 'Unchanged polls must retain card nodes');
medals = { easy: true, chimps: true };
run();
assert.equal(renders, 2, 'An earned medal must refresh visible cards');
nodes['#maps-search'].value = 'nothing'; run();
assert.equal(renders, 3, 'Search changes must refresh');
hidden = true; medals = { easy: false, chimps: false }; run();
assert.equal(renders, 3, 'Background updates must not rebuild hidden maps');
hidden = false; run();
assert.equal(renders, 4, 'Opening Maps must display background medal changes');

const renderHeader = source.slice(source.indexOf('function render() {'), source.indexOf('  const next = mapChoices.find', source.indexOf('function render() {')));
const badge = { textContent: '' };
const counts = {
  state: { theme: 'light' }, detectedProgress: { maps: { logs: { blackBorder: false } } },
  mapChoices: [{ name: 'Logs' }], isMapDone: () => false,
  document: { documentElement: { dataset: {} }, querySelector: selector => selector === '#queue-count' ? badge : {} },
  renderMaps() {}, renderTowers() {}, renderAchievements() {}, renderBossHub() {}
};
vm.createContext(counts);
vm.runInContext(renderHeader + '\n}\nrender();', counts);
assert.equal(badge.textContent, 1, 'The map navigation badge must refresh independently of hidden cards');
console.log('Hidden map rendering, unchanged polls, search and medal refresh checks passed');
