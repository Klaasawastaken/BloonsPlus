const { execFile } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

// Renders the BloonsTD6 window to a PNG using Win32 PrintWindow (PW_RENDERFULLCONTENT),
// which works for hardware-accelerated windows unlike a plain BitBlt/screen-region grab.
// Runs entirely through PowerShell/.NET so no native Node addon or build step is needed.
// SetProcessDPIAware is required so GetClientRect/PrintWindow return real physical pixels —
// without it Windows DPI-virtualizes coordinates for this process, which silently disagreed
// with input.js's (DPI-aware) coordinate space (a consistent ~1.75x mismatch on a 175%-scaled
// 4K display, confirmed empirically: virtualized client rect was 2194×1234 vs real 3840×2160).
// A minimized window reports a zero-size client rect (confirmed live) — restore it first (no
// SetForegroundWindow needed here, PrintWindow can capture a background window's real content).
// PrintWindow draws the whole window, title bar and borders included, from the window rect's
// origin. Windowed BTD6 therefore has to be rendered at full window size and cropped to the client
// area, so capture pixel (x, y) is always game/client pixel (x, y).
const CAPTURE_SCRIPT = `
Add-Type -AssemblyName System.Drawing
Add-Type -Namespace Win32 -Name Capture -MemberDefinition @"
[DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
[DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr hWnd, out RECT lpRect);
[DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
[DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr hWnd, ref POINT lpPoint);
[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
[DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
public struct POINT { public int X; public int Y; }
"@
[Win32.Capture]::SetProcessDPIAware() | Out-Null
$proc = Get-Process -Name BloonsTD6 -ErrorAction SilentlyContinue | Select-Object -First 1
$hwnd = if ($proc) { $proc.MainWindowHandle } else { [IntPtr]::Zero }
if ($hwnd -eq [IntPtr]::Zero) { $hwnd = [Win32.Capture]::FindWindow($null, 'BloonsTD6') }
if ($hwnd -eq [IntPtr]::Zero) { Write-Output '{"error":"window-not-found"}'; exit }
if ([Win32.Capture]::IsIconic($hwnd)) {
  [Win32.Capture]::ShowWindow($hwnd, 9) | Out-Null
  Start-Sleep -Milliseconds 300
}
$rect = New-Object Win32.Capture+RECT
[Win32.Capture]::GetClientRect($hwnd, [ref]$rect) | Out-Null
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0 -or $height -le 0) { Write-Output '{"error":"zero-size"}'; exit }
$outer = New-Object Win32.Capture+RECT
[Win32.Capture]::GetWindowRect($hwnd, [ref]$outer) | Out-Null
$origin = New-Object Win32.Capture+POINT
[Win32.Capture]::ClientToScreen($hwnd, [ref]$origin) | Out-Null
$outerWidth = [Math]::Max($width, $outer.Right - $outer.Left)
$outerHeight = [Math]::Max($height, $outer.Bottom - $outer.Top)
$offsetX = [Math]::Min([Math]::Max(0, $origin.X - $outer.Left), $outerWidth - $width)
$offsetY = [Math]::Min([Math]::Max(0, $origin.Y - $outer.Top), $outerHeight - $height)
$full = New-Object System.Drawing.Bitmap $outerWidth, $outerHeight
$graphics = [System.Drawing.Graphics]::FromImage($full)
$hdc = $graphics.GetHdc()
$ok = [Win32.Capture]::PrintWindow($hwnd, $hdc, 2)
$graphics.ReleaseHdc($hdc)
$graphics.Dispose()
if (-not $ok) { $full.Dispose(); Write-Output '{"error":"printwindow-failed"}'; exit }
$bitmap = $full.Clone((New-Object System.Drawing.Rectangle $offsetX, $offsetY, $width, $height), $full.PixelFormat)
$full.Dispose()
$bitmap.Save('__OUT_PATH__', [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
Write-Output ('{"width":' + $width + ',"height":' + $height + ',"offsetX":' + $offsetX + ',"offsetY":' + $offsetY + '}')
`;

let captureCounter = 0;
function captureWindow() {
  return new Promise((resolve, reject) => {
    if (process.platform !== 'win32') return reject(new Error('Window capture requires Windows'));
    // Unique per call: the passive scan and an automation job can capture at the same time.
    const outPath = path.join(os.tmpdir(), `bloons-plus-capture-${process.pid}-${++captureCounter}.png`);
    const script = CAPTURE_SCRIPT.replace('__OUT_PATH__', outPath.replace(/\\/g, '\\\\'));
    execFile('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', script], { windowsHide: true, timeout: 8000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
      if (error) return reject(new Error('Capture script failed'));
      let meta;
      try { meta = JSON.parse(stdout.trim()); } catch { return reject(new Error('Capture script returned unreadable output')); }
      if (meta.error) return reject(new Error(meta.error));
      fs.readFile(outPath, (readError, buffer) => {
        fs.unlink(outPath, () => {});
        if (readError) return reject(new Error('Could not read capture output'));
        resolve({ width: meta.width, height: meta.height, png: buffer });
      });
    });
  });
}

// Brings the BTD6 window to the OS foreground. Needed before sending virtual-controller input:
// Steam Input's per-game override only routes to the window that actually has OS focus, and
// that's easily lost (e.g. while the user is typing to this session in another window).
const FOCUS_SCRIPT = `
Add-Type -Namespace Win32 -Name Focus -MemberDefinition @"
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
"@
$proc = Get-Process -Name BloonsTD6 -ErrorAction SilentlyContinue | Select-Object -First 1
$hwnd = if ($proc) { $proc.MainWindowHandle } else { [IntPtr]::Zero }
if ($hwnd -eq [IntPtr]::Zero) { $hwnd = [Win32.Focus]::FindWindow($null, 'BloonsTD6') }
if ($hwnd -eq [IntPtr]::Zero) { Write-Output '{"error":"window-not-found"}'; exit }
[Win32.Focus]::ShowWindow($hwnd, 9) | Out-Null
$ok = [Win32.Focus]::SetForegroundWindow($hwnd)
Write-Output ('{"focused":' + $ok.ToString().ToLower() + '}')
`;

function focusWindow() {
  return new Promise((resolve, reject) => {
    if (process.platform !== 'win32') return reject(new Error('Window focus requires Windows'));
    execFile('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', FOCUS_SCRIPT], { windowsHide: true, timeout: 5000 }, (error, stdout) => {
      if (error) return reject(new Error('Focus script failed'));
      let result;
      try { result = JSON.parse(stdout.trim()); } catch { return reject(new Error('Focus script returned unreadable output')); }
      if (result.error) return reject(new Error(result.error));
      resolve(result.focused);
    });
  });
}

// The game's client area (content without title bar/borders) in physical screen coordinates.
// Windowed engines that address the outer window need this to know how far the content is inset.
const CLIENT_GEOMETRY_SCRIPT = `
Add-Type -Namespace Win32 -Name Geometry -MemberDefinition @"
[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
[DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr hWnd, out RECT lpRect);
[DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr hWnd, ref POINT lpPoint);
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
public struct POINT { public int X; public int Y; }
"@
[Win32.Geometry]::SetProcessDPIAware() | Out-Null
$proc = Get-Process -Name BloonsTD6 -ErrorAction SilentlyContinue | Select-Object -First 1
$hwnd = if ($proc) { $proc.MainWindowHandle } else { [IntPtr]::Zero }
if ($hwnd -eq [IntPtr]::Zero) { $hwnd = [Win32.Geometry]::FindWindow($null, 'BloonsTD6') }
if ($hwnd -eq [IntPtr]::Zero) { Write-Output '{"error":"window-not-found"}'; exit }
$rect = New-Object Win32.Geometry+RECT
[Win32.Geometry]::GetClientRect($hwnd, [ref]$rect) | Out-Null
$origin = New-Object Win32.Geometry+POINT
[Win32.Geometry]::ClientToScreen($hwnd, [ref]$origin) | Out-Null
Write-Output ('{"x":' + $origin.X + ',"y":' + $origin.Y + ',"width":' + ($rect.Right - $rect.Left) + ',"height":' + ($rect.Bottom - $rect.Top) + '}')
`;

function getClientGeometry() {
  return new Promise((resolve, reject) => {
    if (process.platform !== 'win32') return reject(new Error('Window geometry requires Windows'));
    execFile('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', CLIENT_GEOMETRY_SCRIPT], { windowsHide: true, timeout: 5000 }, (error, stdout) => {
      if (error) return reject(new Error('Geometry script failed'));
      let result;
      try { result = JSON.parse(stdout.trim()); } catch { return reject(new Error('Geometry script returned unreadable output')); }
      if (result.error) return reject(new Error(result.error));
      resolve(result);
    });
  });
}

module.exports = { captureWindow, focusWindow, getClientGeometry };
