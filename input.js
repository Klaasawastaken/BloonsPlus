// Real mouse/keyboard input (per explicit user direction, after the ViGEmBus virtual-controller
// + Steam Input path proved unreliable: intermittent input delivery, and the in-game cursor
// turned out invisible to both PrintWindow and screen-grab capture, so it couldn't be tracked
// either). Movement is still smooth/eased, never a teleport — an eased multi-step SetCursorPos
// walk, run entirely inside one PowerShell invocation (self-contained, no per-step process
// spawn overhead). Coordinates are BTD6 client-area coordinates (matching capture.js), converted
// to screen coordinates via ClientToScreen.
const { execFile } = require('node:child_process');
const { focusWindow } = require('./capture');

function run(script, timeout = 8000) {
  return new Promise((resolve, reject) => {
    execFile('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', script], { windowsHide: true, timeout, maxBuffer: 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) return reject(new Error(stderr?.trim() || error.message));
      resolve(stdout.trim());
    });
  });
}

// SetProcessDPIAware makes coordinates match capture.js's (also DPI-aware) real physical
// pixels — without it, ClientToScreen/Cursor.Position silently disagree with the capture's
// coordinate space (confirmed empirically: ~1.75x mismatch on this 175%-scaled 4K display).
const COMMON_TYPES = `
Add-Type -Namespace Win32 -Name Input -MemberDefinition @"
[DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr hWnd, ref POINT lpPoint);
[DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, int dx, int dy, int dwData, UIntPtr dwExtraInfo);
[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
public struct POINT { public int X; public int Y; }
"@
[Win32.Input]::SetProcessDPIAware() | Out-Null
function Get-Btd6Window {
  $proc = Get-Process -Name BloonsTD6 -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $proc) { throw "BTD6 window not found" }
  $hwnd = $proc.MainWindowHandle
  if ($hwnd -eq [IntPtr]::Zero) { $hwnd = [Win32.Input]::FindWindow($null, 'BloonsTD6') }
  if ($hwnd -eq [IntPtr]::Zero) { throw "BTD6 window not found" }
  return $hwnd
}
function ClientToScreenPoint($hwnd, $x, $y) {
  $pt = New-Object Win32.Input+POINT
  $pt.X = $x; $pt.Y = $y
  [Win32.Input]::ClientToScreen($hwnd, [ref]$pt) | Out-Null
  return $pt
}
`;

// Eases from wherever the real cursor currently is to (x, y) in BTD6 client coordinates, over
// durationMs, using ease-in-out so it settles rather than stopping abruptly.
async function moveMouseTo(x, y, { durationMs = 350, steps } = {}) {
  await focusWindow();
  const stepCount = steps || Math.max(6, Math.round(durationMs / 16));
  const script = `
Add-Type -AssemblyName System.Windows.Forms
${COMMON_TYPES}
$hwnd = Get-Btd6Window
$target = ClientToScreenPoint $hwnd ${Math.round(x)} ${Math.round(y)}
$start = [System.Windows.Forms.Cursor]::Position
$steps = ${stepCount}
$stepDelayMs = [Math]::Max(1, [Math]::Round(${durationMs} / $steps))
for ($i = 1; $i -le $steps; $i++) {
  $t = $i / $steps
  $eased = if ($t -lt 0.5) { 4 * $t * $t * $t } else { 1 - [Math]::Pow(-2 * $t + 2, 3) / 2 }
  $px = [int]($start.X + ($target.X - $start.X) * $eased)
  $py = [int]($start.Y + ($target.Y - $start.Y) * $eased)
  [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($px, $py)
  Start-Sleep -Milliseconds $stepDelayMs
}
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($target.X, $target.Y)
Write-Output "ok"
`;
  await run(script, durationMs + 5000);
}

async function click({ button = 'left', holdMs = 60 } = {}) {
  await focusWindow();
  const MOUSEEVENTF_LEFTDOWN = 0x0002, MOUSEEVENTF_LEFTUP = 0x0004;
  const MOUSEEVENTF_RIGHTDOWN = 0x0008, MOUSEEVENTF_RIGHTUP = 0x0010;
  const down = button === 'right' ? MOUSEEVENTF_RIGHTDOWN : MOUSEEVENTF_LEFTDOWN;
  const up = button === 'right' ? MOUSEEVENTF_RIGHTUP : MOUSEEVENTF_LEFTUP;
  const script = `
${COMMON_TYPES}
[Win32.Input]::mouse_event(${down}, 0, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds ${holdMs}
[Win32.Input]::mouse_event(${up}, 0, 0, 0, [UIntPtr]::Zero)
Write-Output "ok"
`;
  await run(script);
}

async function scroll(ticks, direction = 'down') {
  await focusWindow();
  const MOUSEEVENTF_WHEEL = 0x0800;
  const delta = (direction === 'down' ? -120 : 120) * ticks;
  const script = `
${COMMON_TYPES}
[Win32.Input]::mouse_event(${MOUSEEVENTF_WHEEL}, 0, 0, ${delta}, [UIntPtr]::Zero)
Write-Output "ok"
`;
  await run(script);
}

async function moveAndClick(x, y, opts = {}) {
  await moveMouseTo(x, y, opts);
  await click(opts);
}

// Types text into whatever field currently has focus (e.g. after clicking a search box).
// SendKeys treats + ^ % ~ ( ) { } [ ] as special, so they're escaped into literal braces.
async function typeText(text) {
  await focusWindow();
  const escaped = text.replace(/([+^%~(){}[\]])/g, '{$1}');
  const script = `
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait('${escaped.replace(/'/g, "''")}')
Write-Output "ok"
`;
  await run(script);
}

// Selects-all and deletes whatever's in the currently-focused field.
async function clearField() {
  await focusWindow();
  const script = `
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait('^a')
[System.Windows.Forms.SendKeys]::SendWait('{DEL}')
Write-Output "ok"
`;
  await run(script);
}

module.exports = { moveMouseTo, click, scroll, moveAndClick, typeText, clearField };
