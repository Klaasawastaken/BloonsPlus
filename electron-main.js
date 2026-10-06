const { app, BrowserWindow, shell, nativeTheme, dialog } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const ICON_PATH = path.join(__dirname, 'bloonsplus.ico');

const port = Number(process.env.PORT || 4173);
const softwareRendering = fs.existsSync('C:\\Windows\\AppSandbox\\appsandbox-agent.exe') || process.env.BLOONS_SOFTWARE_RENDERING === '1';
const url = `http://127.0.0.1:${port}/${softwareRendering ? '?softwareRendering=1' : ''}`;
const setupOnly = process.env.BLOONS_SETUP_ONLY === '1';
const fileJournal = path.resolve(__dirname, '..', '..', '.bloons-setup', 'app-file-transaction.json');
const fileRecoveryPending = app.isPackaged && (fs.existsSync(fileJournal) || fs.existsSync(fileJournal + '.next'));

// The App Sandbox VM shares one GPU passthrough device between BTD6 (a full 3D game) and
// Electron's own GPU process. Under contention (both starting around the same time on a fresh
// boot) Electron's GPU process can fail to negotiate and app.whenReady() never resolves - the
// main process stays alive and "Responding" with no window and no error. Running without GPU
// acceleration avoids that negotiation entirely; this app is a plain settings/status UI with no
// need for it.
// The guest needs software rendering for GPU passthrough stability. The host
// should retain Chromium's compositor for smooth scrolling and video previews.
if (softwareRendering) {
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

// A package interrupted between file replacements must be recovered by the
// installation owner before loading a possibly mixed controller version.
if (!fileRecoveryPending) require('./server.js'); // starts the local server as a side effect

function loadWithRetry(win, attempt = 0) {
  if (win.isDestroyed()) return;
  win.loadURL(url).catch(() => {
    if (win.isDestroyed()) return;
    if (attempt >= 20) {
      const background=nativeTheme.shouldUseDarkColors?'#11192b':'#f5f7fc';
      const text=nativeTheme.shouldUseDarkColors?'#eef2fb':'#1e2a52';
      const recovery=`<!doctype html><html><meta charset="utf-8"><title>Bloons+ connection</title><body style="margin:0;background:${background};color:${text};font:16px system-ui;display:grid;place-items:center;height:100vh"><main style="max-width:480px;padding:36px"><h1>Bloons+</h1><p>The local controller did not start. Your VM and replay have not been stopped.</p><p>Reopen the app or retry when the controller is ready.</p><a style="color:${text}" href="${url}">Retry connection</a></main></body></html>`;
      win.loadURL('data:text/html;charset=utf-8,'+encodeURIComponent(recovery)).catch(error=>logCrash('startup-recovery',error.message));return;
    }
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
    backgroundColor: nativeTheme.shouldUseDarkColors ? '#11192b' : '#f5f7fc',
    icon: ICON_PATH,
  });
  win.webContents.setWindowOpenHandler(({ url: target }) => {
    try {
      const external = new URL(target);
      if (external.protocol === 'https:') shell.openExternal(external.href).catch(error => logCrash('external-link', error.message));
    } catch { /* Reject malformed or non-web links. */ }
    return { action: 'deny' };
  });
  win.webContents.on('will-navigate',(event,target)=>{
    if (win.webContents.getURL().startsWith('data:text/html') && target===url) {
      event.preventDefault();loadWithRetry(win);
    }
  });
  if (process.platform === 'win32') win.setAppDetails({
    appId: 'com.bloonsplus.app',
    relaunchIcon: `${ICON_PATH},0`,
    relaunchDisplayName: 'Bloons+',
  });
  loadWithRetry(win);
}

app.whenReady().then(() => {
  if (fileRecoveryPending) {
    if (!setupOnly) dialog.showErrorBox('Bloons+ setup needs recovery',
      'App file installation was interrupted. Reopen the Bloons+ installer and choose Continue setup or Repair before opening the app. Your saved progress is retained.');
    app.exit(1);
    return;
  }
  // Windows groups/labels the taskbar entry by this id; without it Electron falls back to the
  // executable path, which can pick up a generic icon instead of the one set on the window.
  if (process.platform === 'win32') app.setAppUserModelId('com.bloonsplus.app');
  if (!setupOnly) createWindow();
  app.on('activate', () => { if (!setupOnly && BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
