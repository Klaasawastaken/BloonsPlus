const assert = require('node:assert/strict');
const { privateStaticPath } = require('../lib/static-access');
for (const name of ['private/discord-bot/index.js', 'PRIVATE/discord-bot/index.js', '.git/config', 'lib/automation.js', 'autobtd6/Profile.Save', 'dist/BloonsPlusPayload.zip', 'host-server.log', '.env', 'private\\discord-bot\\index.js']) {
  assert.equal(privateStaticPath(name), true, name);
}
for (const name of ['index.html', 'assets/app/app.js', 'assets/app/styles.css', 'assets/logo.svg', 'data/catalogs/map-catalog.js', 'data/config/map-order.json', 'map-icons/cubism.png', 'tower-icons/dart-monkey.png', 'data/tower-upgrades.json']) {
  assert.equal(privateStaticPath(name), false, name);
}
console.log('Private static-path checks passed.');
