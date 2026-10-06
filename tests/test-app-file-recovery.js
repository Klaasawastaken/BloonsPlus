const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync('electron-main.js', 'utf8');

async function run({pending, setupOnly = false, packaged = true}) {
  const calls = {server: 0, dialogs: [], exits: []};
  const app = {
    isPackaged: packaged, disableHardwareAcceleration() {}, commandLine: {appendSwitch() {}},
    on() {}, whenReady: () => Promise.resolve(), setAppUserModelId() {},
    exit: code => calls.exits.push(code), quit() {}
  };
  class BrowserWindow {
    static getAllWindows() {return [];}
    constructor() {this.webContents = {setWindowOpenHandler() {}, on() {}};}
    isDestroyed() {return false;}
    setAppDetails() {}
    loadURL() {return Promise.resolve();}
  }
  const electron = {app, BrowserWindow, shell: {}, nativeTheme: {shouldUseDarkColors: false},
    dialog: {showErrorBox: (title, message) => calls.dialogs.push({title, message})}};
  vm.runInNewContext(source, {
    __dirname: path.resolve('fixture-install/resources/app'),
    process: {env: {BLOONS_SETUP_ONLY: setupOnly ? '1' : '0'}, platform: 'win32', on() {}},
    require: name => {
      if (name === 'electron') return electron;
      if (name === 'node:path') return path;
      if (name === 'node:fs') return {existsSync: file => pending && /app-file-transaction\.json(?:\.next)?$/.test(file), appendFileSync() {}};
      if (name === './server.js') {calls.server++; return {};}
      throw new Error('Unexpected module ' + name);
    }, setTimeout() {}
  });
  await Promise.resolve();
  return calls;
}

(async () => {
  for (const setupOnly of [false, true]) {
    const interrupted = await run({pending: true, setupOnly});
    assert.equal(interrupted.server, 0, 'Interrupted package started the possibly mixed controller');
    assert.deepEqual(interrupted.exits, [1]);
    if (!setupOnly) assert.match(interrupted.dialogs[0].message, /Continue setup.*repair/i);
    else assert.equal(interrupted.dialogs.length, 0, 'Silent setup opened an interactive dialog');
  }
  assert.equal((await run({pending: false, setupOnly: true})).server, 1);
  assert.equal((await run({pending: true, setupOnly: true, packaged: false})).server, 1, 'Installed-file guard changed dev startup');
  console.log('App file recovery: pending package blocks controller startup; normal and dev startup preserved');
})().catch(error => {console.error(error); process.exitCode = 1;});
