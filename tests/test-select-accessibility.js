// Exercise the production enhancer in an isolated, hidden Chromium renderer.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const rendererChecks = async () => {
  const check = (value, message) => {if (!value) throw new Error(message);};
  const tick = () => new Promise(resolve => setTimeout(resolve, 0));
  const select = document.querySelector('#mode'), button = select.nextElementSibling;
  const legendButton = document.querySelector('#legend').nextElementSibling;
  const outer = document.querySelector('#outer'), inner = document.querySelector('#inner');
  let changes = 0; select.addEventListener('change', () => changes++);
  check(select.matches(':disabled') && !select.disabled, 'Fixture must exercise inherited native disablement');
  check(button.matches(':disabled'), 'Disabled fieldset must keep its visible control unavailable');
  button.click(); check(!document.querySelector('.app-select-menu'), 'Disabled control opened a menu');
  check(!legendButton.disabled, 'First legend exception was lost');
  outer.disabled = false; await tick();
  check(!button.disabled, 'Fieldset enablement did not refresh the control');
  button.click(); let row = document.querySelector('[data-option-index="1"]');
  check(row && !row.disabled, 'Enabled dropdown did not expose Hard');
  inner.disabled = true;
  row.click();
  check(select.value === 'easy' && changes === 0, 'A stale open row bypassed fieldset disablement');
  await tick();
  check(button.disabled && button.getAttribute('aria-expanded') === 'false', 'Disabled open control remained expanded');
  check(!document.querySelector('.app-select-menu'), 'Disabled control retained its menu');
  inner.disabled = false; await tick(); button.click();
  row = document.querySelector('[data-option-index="1"]');
  select.querySelector('optgroup').disabled = true;
  row.click();
  check(select.value === 'easy' && changes === 0, 'A stale option bypassed disabled optgroup');
  await tick(); select.querySelector('optgroup').disabled = false; await tick();
  row = document.querySelector('[data-option-index="1"]');
  row.click();
  check(select.value === 'hard' && changes === 1, 'Re-enabled option lost native value/change semantics');
  check(button.getAttribute('aria-expanded') === 'false', 'Successful selection left menu expanded');
  return {inheritedDisabled:true, legendException:true, dynamicRefresh:true, staleRows:true, nativeChange:true};
};
const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-select-'));
const main = path.join(folder, 'checks.js');
const resultPath = path.join(folder, 'result.json');
const electronPath = require('electron');
const sourcePath = path.resolve('assets/app/select-controls.js');
fs.writeFileSync(main, `
const {app, BrowserWindow} = require('electron');
const fs = require('node:fs');
const report = value => fs.writeFileSync(${JSON.stringify(resultPath)}, JSON.stringify(value));
process.on('uncaughtException', error => {report({error:error.stack}); app.exit(1);});
app.setPath('userData', ${JSON.stringify(folder)});
app.setPath('sessionData', ${JSON.stringify(folder)});
app.setPath('logs', ${JSON.stringify(folder)});
app.disableHardwareAcceleration();
app.commandLine.appendSwitch('no-sandbox');
app.whenReady().then(async () => {
  const win = new BrowserWindow({show:false, webPreferences:{contextIsolation:true, sandbox:true}});
  try {
    await win.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(
      '<fieldset id="outer" disabled><legend><label>Legend <select id="legend"><option>Allowed</option></select></label></legend>' +
      '<fieldset id="inner"><label>Mode <select id="mode"><optgroup label="Modes"><option value="easy">Easy</option><option value="hard">Hard</option></optgroup></select></label></fieldset></fieldset>'
    ));
    await win.webContents.executeJavaScript(fs.readFileSync(${JSON.stringify(sourcePath)}, 'utf8'));
    const result = await win.webContents.executeJavaScript(${JSON.stringify('(' + rendererChecks.toString() + ')()')});
    report(result);
    win.destroy(); app.exit(0);
  } catch (error) { report({error:error.stack}); win.destroy(); app.exit(1); }
}).catch(error => {report({error:error.stack}); app.exit(1);});
`);
try {
  const environment = {...process.env}; delete environment.ELECTRON_RUN_AS_NODE;
  const run = spawnSync(electronPath, [main], {env:environment, windowsHide:true, timeout:30000, encoding:'utf8'});
  const result = fs.existsSync(resultPath) ? fs.readFileSync(resultPath, 'utf8') : 'Renderer produced no result';
  assert.equal(run.status, 0, (run.error?.message || '') + result + run.stdout + run.stderr);
  assert.equal(JSON.parse(result).inheritedDisabled, true);
  console.log('Dropdown accessibility: real disabled fieldsets, legend exception, dynamic refresh and stale rows passed');
} finally {
  const resolved = path.resolve(folder);
  if (!resolved.startsWith(path.resolve(os.tmpdir()) + path.sep) || !path.basename(resolved).startsWith('bloons-select-'))
    throw new Error('Unsafe renderer fixture cleanup path');
  fs.rmSync(resolved, {recursive:true, force:true});
}
