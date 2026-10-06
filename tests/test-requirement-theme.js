// Render the production stylesheet in an isolated, hidden Chromium instance.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const checks = () => {
  const rgb = value => value.match(/[\d.]+/g).map(Number);
  const over = (front, back) => front.slice(0, 3).map((v, i) => v * (front[3] ?? 1) + back[i] * (1 - (front[3] ?? 1)));
  const luminance = color => color.slice(0, 3).map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
  const contrast = (a, b) => (Math.max(luminance(a), luminance(b)) + .05) / (Math.min(luminance(a), luminance(b)) + .05);
  const row = document.querySelector('.requirement-item');
  const parent = rgb(getComputedStyle(row.parentElement).backgroundColor);
  const background = over(rgb(getComputedStyle(row).backgroundColor), parent);
  const ratios = Array.from(row.querySelectorAll('span,b')).map(e => contrast(rgb(getComputedStyle(e).color), background));
  if (Math.min(...ratios) < 4.5) throw Error('Dark requirement text contrast below 4.5: ' + JSON.stringify(ratios));
  const tierRow = document.querySelector('.requirement-path-row');
  const boxes = Array.from(tierRow.querySelectorAll('.tier-pill')).map(e => e.getBoundingClientRect());
  if (boxes.length !== 5 || boxes.some(box => Math.abs(box.top - boxes[0].top) > 1)) throw Error('T1–T5 must remain on one row');
  return {ratios, tiersInOneRow: true, viewportWidth: window.innerWidth};
};
const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-requirement-theme-'));
const main = path.join(folder, 'checks.cjs'), resultPath = path.join(folder, 'result.json');
const css = fs.readFileSync('assets/app/styles.css', 'utf8');
const html = '<!doctype html><html data-theme="dark"><head><style>' + css + '</style></head><body>' +
  '<main><section id="automation" class="view compact-map-workspace"><div class="panel map-requirements-panel"><div class="requirements-list">' +
  '<div class="requirement-item"><i class="requirement-mark valid">✓</i><span>Medal state read</span><b>Already completed</b></div></div>' +
  '<article class="tower-requirement-card"><div class="requirement-path-row"><b>Path 1</b>' +
  [1, 2, 3, 4, 5].map(tier => '<span class="tier-pill valid">✓ T' + tier + '</span>').join('') +
  '</div></article></div></section></main></body></html>';
fs.writeFileSync(main, `
const {app,BrowserWindow}=require('electron');
const fs=require('node:fs');
const report=value=>fs.writeFileSync(${JSON.stringify(resultPath)},JSON.stringify(value));
app.setPath('userData',${JSON.stringify(folder)});app.setPath('sessionData',${JSON.stringify(folder)});app.setPath('logs',${JSON.stringify(folder)});
app.disableHardwareAcceleration();app.commandLine.appendSwitch('no-sandbox');
app.whenReady().then(async()=>{
 const win=new BrowserWindow({show:false,width:1280,height:800,webPreferences:{contextIsolation:true,sandbox:true}});
 win.webContents.on('console-message',(_event,level,message)=>{if(level>=2)console.error(message);});
 let narrowWin;
 try{
  await win.loadURL('data:text/html;charset=utf-8,'+encodeURIComponent(${JSON.stringify(html)}));
  const desktop=await win.webContents.executeJavaScript(${JSON.stringify('(' + checks.toString() + ')()')});
  narrowWin=new BrowserWindow({show:false,width:620,height:800,webPreferences:{contextIsolation:true,sandbox:true}});
  narrowWin.webContents.on('console-message',(_event,level,message)=>{if(level>=2)console.error(message);});
  await narrowWin.loadURL('data:text/html;charset=utf-8,'+encodeURIComponent(${JSON.stringify(html)}));
  const narrow=await narrowWin.webContents.executeJavaScript(${JSON.stringify('(' + checks.toString() + ')()')});
  if(narrow.viewportWidth>620)throw Error('Narrow viewport was not applied');
  const lightBackground=await win.webContents.executeJavaScript("document.documentElement.dataset.theme='light';getComputedStyle(document.querySelector('.requirement-item')).backgroundColor");
  if(lightBackground!=='rgba(255, 255, 255, 0.345)')throw Error('Light requirement surface changed');
  report({desktop,narrow});narrowWin.destroy();win.destroy();app.exit(0);
 }catch(error){report({error:error.stack});if(narrowWin)narrowWin.destroy();win.destroy();app.exit(1);}
}).catch(error=>{report({error:error.stack});app.exit(1);});
`);
try {
  const environment = {...process.env}; delete environment.ELECTRON_RUN_AS_NODE;
  const run = spawnSync(require('electron'), [main], {env:environment,windowsHide:true,timeout:30000,encoding:'utf8'});
  const result = fs.existsSync(resultPath) ? fs.readFileSync(resultPath, 'utf8') : 'Renderer produced no result';
  assert.equal(run.status, 0, result + run.stdout + run.stderr);
  const measured = JSON.parse(result);
  assert.equal(measured.narrow.tiersInOneRow, true);
  console.log('Dark requirement contrast, single-row T1–T5 and preserved light surface passed: ' + JSON.stringify(measured));
} finally {
  const resolved = path.resolve(folder);
  if (!resolved.startsWith(path.resolve(os.tmpdir()) + path.sep) || !path.basename(resolved).startsWith('bloons-requirement-theme-')) throw Error('Unsafe fixture cleanup path');
  fs.rmSync(resolved, {recursive:true,force:true});
}
