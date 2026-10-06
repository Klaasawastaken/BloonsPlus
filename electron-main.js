const { app, BrowserWindow, shell } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const ICON_PATH = path.join(__dirname, 'bloonsplus.ico');

const port = Number(process.env.PORT || 4173);
const url = `http://127.0.0.1:${port}`;
const setupOnly = process.env.BLOONS_SETUP_ONLY === '1';

// The App Sandbox VM shares one GPU passthrough device between BTD6 (a full 3D game) and
// Electron's own GPU process. Under contention (both starting around the same time on a fresh
// boot) Electron's GPU process can fail to negotiate and app.whenReady() never resolves - the
// main process stays alive and "Responding" with no window and no error. Running without GPU
// acceleration avoids that negotiation entirely; this app is a plain settings/status UI with no
// need for it.
// The guest needs software rendering for GPU passthrough stability. The host
// should retain Chromium's compositor for smooth scrolling and video previews.
if (fs.existsSync('C:\\Windows\\AppSandbox\\appsandbox-agent.exe') || process.env.BLOONS_SOFTWARE_RENDERING === '1') {
  app.disableHardwareAcceleration();
}
app.commandLine.appendSwitch('no-sandbox');

const CRASH_LOG = path.join(__dirname, 'electron-crash.log');
function logCrash(label, detail) {
  try { fs.appendFileSync(CRASH_LOG, `[${new Date().toISOString()}] ${label}: ${detail}\n`); } catch { /* best effort */ }
}
process.on('uncaughtException', error => logCrash('uncaughtException', error.stack || error.message));
app.on('render-process-gone', (_event, _wc, details) => logCrash('render-process-gone', JSON.stringify(details)));
app.on('child-process-gone', (_event, details) => logCrash('child-process-gone', JSON.stringify(details)));

require('./server.js'); // starts the local server as a side effect

function loadWithRetry(win, attempt = 0) {
  win.loadURL(url).catch(() => {
    if (attempt >= 20) return;
    setTimeout(() => loadWithRetry(win, attempt + 1), 200);
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1080,
    minHeight: 680,
    title: 'Bloons+',
    autoHideMenuBar: true,
    backgroundColor: '#f5f6f1',
    icon: ICON_PATH,
  });
  win.webContents.setWindowOpenHandler(({ url: target }) => {
    try {
      const external = new URL(target);
      if (external.protocol === 'https:') shell.openExternal(external.href).catch(error => logCrash('external-link', error.message));
    } catch { /* Reject malformed or non-web links. */ }
    return { action: 'deny' };
  });
  if (process.platform === 'win32') win.setAppDetails({
    appId: 'com.bloonsplus.app',
    relaunchIcon: `${ICON_PATH},0`,
    relaunchDisplayName: 'Bloons+',
  });
  loadWithRetry(win);
}

app.whenReady().then(() => {
  // Windows groups/labels the taskbar entry by this id; without it Electron falls back to the
  // executable path, which can pick up a generic icon instead of the one set on the window.
  if (process.platform === 'win32') app.setAppUserModelId('com.bloonsplus.app');
  if (!setupOnly) createWindow();
  app.on('activate', () => { if (!setupOnly && BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
