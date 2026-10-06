"""Present BTD6's client area as a 1080p or 1440p game to AutoBTD6.

AutoBTD6's screenshots, templates and recorded clicks use game coordinates. In
windowed mode those must be translated to the client rectangle, not the desktop.
The patch changes only PyAutoGUI calls made by this process; it does not modify
the game or its files.
"""
import ctypes
from ctypes import wintypes
from contextlib import contextmanager
import os
import time
import inspect

import pyautogui

_user32 = ctypes.windll.user32
try:
    _user32.SetProcessDPIAware()
except OSError:
    pass

_real_size = pyautogui.size
_real_screenshot = pyautogui.screenshot
_real_move_to = pyautogui.moveTo
_real_click = pyautogui.click
_click_signature = inspect.signature(_real_click)
_real_drag_to = pyautogui.dragTo


class _Point(ctypes.Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)]


class _Rect(ctypes.Structure):
    _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG),
                ('right', wintypes.LONG), ('bottom', wintypes.LONG)]


_user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
_user32.FindWindowW.restype = wintypes.HWND
_user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(_Rect)]
_user32.GetClientRect.restype = wintypes.BOOL
_user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(_Point)]
_user32.ClientToScreen.restype = wintypes.BOOL
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL
_user32.IsWindow.argtypes = [wintypes.HWND]
_user32.IsWindow.restype = wintypes.BOOL
_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.IsIconic.restype = wintypes.BOOL
_user32.GetForegroundWindow.argtypes = []
_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.restype = wintypes.BOOL
_user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.ShowWindow.restype = wintypes.BOOL
_kernel32 = ctypes.windll.kernel32
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
_kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL

_cached_hwnd = None


def _find_game_window():
    global _cached_hwnd
    if _cached_hwnd and _user32.IsWindow(_cached_hwnd):
        rect = _Rect()
        if _user32.GetClientRect(_cached_hwnd, ctypes.byref(rect)):
            width, height = rect.right - rect.left, rect.bottom - rect.top
            if width >= 640 and height >= 360 and abs(width / height - 16 / 9) <= 0.12:
                return _cached_hwnd
    _cached_hwnd = None
    # There can be several BTD6 top-level windows (for example a small transition
    # window and the actual game window). FindWindowW returns an arbitrary title
    # match, which caused 304x201 to win over the full 16:9 client by accident.
    windows = []
    process_names = {}
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def visit(hwnd, _):
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value not in process_names:
            name = ''
            handle = _kernel32.OpenProcess(0x1000, False, pid.value)
            if handle:
                buffer = ctypes.create_unicode_buffer(32768)
                length = wintypes.DWORD(len(buffer))
                if _kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)):
                    name = os.path.basename(buffer.value).lower()
                _kernel32.CloseHandle(handle)
            process_names[pid.value] = name
        if process_names[pid.value] in ('bloonstd6.exe', 'bloonstd6-epic.exe'):
            rect = _Rect()
            if _user32.GetClientRect(hwnd, ctypes.byref(rect)):
                width, height = rect.right - rect.left, rect.bottom - rect.top
                area = max(0, width) * max(0, height)
                if area:
                    valid = width >= 640 and height >= 360 and abs(width / height - 16 / 9) <= 0.12
                    # Prefer a real-sized 16:9 client; retain the largest invalid
                    # window only as a diagnostic fallback if none is available.
                    windows.append((1 if valid else 0, area, hwnd))
        return True

    _user32.EnumWindows(visit, 0)
    if windows:
        _cached_hwnd = max(windows)[2]
    return _cached_hwnd


def game_client():
    global _cached_hwnd
    last_error = 'BTD6 window not found'
    for attempt in range(12):
        hwnd = _find_game_window()
        if hwnd:
            rect = _Rect()
            point = _Point(0, 0)
            if _user32.IsIconic(hwnd):
                last_error = 'BTD6 window is minimized'
            elif _user32.GetClientRect(hwnd, ctypes.byref(rect)) and _user32.ClientToScreen(hwnd, ctypes.byref(point)):
                width, height = rect.right - rect.left, rect.bottom - rect.top
                if width > 0 and height > 0:
                    if abs(width / height - 16 / 9) > 0.08:
                        last_error = f'BTD6 window is transitioning; ignoring non-game client {width}x{height}'
                        _cached_hwnd = None
                    elif width < 640 or height < 360:
                        last_error = f'BTD6 window is not ready yet ({width}x{height})'
                        _cached_hwnd = None
                    else:
                        return point.x, point.y, width, height
                else:
                    last_error = 'BTD6 window is minimized'
            else:
                last_error = 'Could not read BTD6 client area'
            _cached_hwnd = None
        if attempt < 11:
            time.sleep(0.15)
    raise RuntimeError(last_error)


def _client_with_recovery():
    """Allow a window transition to recover without sending any gameplay clicks."""
    global _cached_hwnd
    transient_errors = {'BTD6 window not found', 'Could not read BTD6 client area', 'BTD6 window is minimized'}
    for recovery in range(10):
        try:
            return game_client()
        except RuntimeError as error:
            reason = str(error)
            transient = reason in transient_errors or reason.startswith('BTD6 window is transitioning') or reason.startswith('BTD6 window is not ready yet')
            if not transient or recovery == 9:
                raise
            _cached_hwnd = None
            restored = focus_game()
            print('RECOVERY capture attempt=' + str(recovery + 1) + '/10 reason=' + reason
                  + ' restored=' + str(restored), flush=True)
            time.sleep(min(0.4 + recovery * 0.1, 1.2))


def game_size():
    _, _, width, height = _client_with_recovery()
    return (1920, 1080) if width < 2240 else (2560, 1440)


def is_game_foreground():
    target = _find_game_window()
    foreground = _user32.GetForegroundWindow()
    if not target or not foreground:
        return False
    target_pid = wintypes.DWORD()
    foreground_pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(target, ctypes.byref(target_pid))
    _user32.GetWindowThreadProcessId(foreground, ctypes.byref(foreground_pid))
    return target_pid.value == foreground_pid.value


def focus_game():
    """Bring BTD6 forward. Windows refuses SetForegroundWindow from a background process
    (focus-steal prevention), and after a VM restart Steam's own window sat on top, so every
    replay failed instantly. Escalate: restore, tap Alt (unlocks foreground changes), attach
    to the foreground window's input thread, and minimise whatever window is blocking."""
    hwnd = _find_game_window()
    if not hwnd:
        return False
    for attempt in range(3):
        _user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        blocker = _user32.GetForegroundWindow()
        if attempt >= 1 and blocker and blocker != hwnd:
            _user32.ShowWindow(blocker, 6)  # SW_MINIMIZE the window in front (Steam, a browser...)
        _user32.keybd_event(0x12, 0, 0, 0)       # Alt down
        _user32.keybd_event(0x12, 0, 0x0002, 0)  # Alt up
        foreground_thread = _user32.GetWindowThreadProcessId(_user32.GetForegroundWindow(), None)
        own_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        attached = foreground_thread and foreground_thread != own_thread and _user32.AttachThreadInput(own_thread, foreground_thread, True)
        try:
            _user32.BringWindowToTop(hwnd)
            _user32.SetForegroundWindow(hwnd)
        finally:
            if attached:
                _user32.AttachThreadInput(own_thread, foreground_thread, False)
        for _ in range(20):
            if is_game_foreground():
                return True
            time.sleep(0.05)
    return False


def _absolute(x, y):
    left, top, width, height = game_client()
    game_width, game_height = ((1920, 1080) if width < 2240 else (2560, 1440))
    return round(left + float(x) * width / game_width), round(top + float(y) * height / game_height)


def _check_input_privileges():
    """UIPI silently discards input sent from a lower-privilege app to an elevated game."""
    if ctypes.windll.shell32.IsUserAnAdmin():
        return
    hwnd = _cached_hwnd
    if not hwnd:
        return
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    process = _kernel32.OpenProcess(0x1000, False, pid.value)
    token = wintypes.HANDLE()
    api = ctypes.WinDLL('advapi32', use_last_error=True)
    api.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    api.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    try:
        if process and api.OpenProcessToken(process, 8, ctypes.byref(token)):
            elevated, length = wintypes.DWORD(), wintypes.DWORD()
            if api.GetTokenInformation(token, 20, ctypes.byref(elevated), ctypes.sizeof(elevated), ctypes.byref(length)) and elevated.value:
                raise RuntimeError('BTD6 runs as administrator but Bloons+ does not. Restart Bloons+ as administrator in the VM so Windows permits game input.')
    finally:
        if token: _kernel32.CloseHandle(token)
        if process: _kernel32.CloseHandle(process)


@contextmanager
def _desktop_size_for_pyautogui():
    # PyAutoGUI's internal movement code clamps coordinates using size(). Keep
    # its real desktop size while sending translated coordinates.
    pyautogui.size = _real_size
    current_move_to = pyautogui.moveTo
    pyautogui.moveTo = _real_move_to
    try:
        yield
    finally:
        pyautogui.moveTo = current_move_to
        pyautogui.size = game_size


def _point_args(args, kwargs):
    args = list(args)
    kwargs = dict(kwargs)
    if args and isinstance(args[0], (tuple, list)):
        x, y = args.pop(0)
        x, y = _absolute(x, y)
        return [x, y, *args], kwargs
    if len(args) >= 2 and args[0] is not None and args[1] is not None:
        args[0], args[1] = _absolute(args[0], args[1])
    elif kwargs.get('x') is not None and kwargs.get('y') is not None:
        kwargs['x'], kwargs['y'] = _absolute(kwargs['x'], kwargs['y'])
    return args, kwargs


def move_to(*args, **kwargs):
    if 'duration' not in kwargs and len(args) < 3:
        kwargs['duration'] = 0.10
    args, kwargs = _point_args(args, kwargs)
    _check_input_privileges()
    with _desktop_size_for_pyautogui():
        result = _real_move_to(*args, **kwargs)
        _deliver_pointer_event()
        return result


def _deliver_pointer_event():
    """Notify raw-input consumers after SetCursorPos-based pointer movement."""
    point = _Point()
    _user32.GetCursorPos(ctypes.byref(point))
    left, top = _user32.GetSystemMetrics(76), _user32.GetSystemMetrics(77)
    width, height = _user32.GetSystemMetrics(78), _user32.GetSystemMetrics(79)
    if width > 1 and height > 1:
        x = round((point.x - left) * 65535 / (width - 1))
        y = round((point.y - top) * 65535 / (height - 1))
        _user32.mouse_event(0x8001 | 0x4000, x, y, 0, 0)


def click(*args, **kwargs):
    args, kwargs = _point_args(args, kwargs)
    _check_input_privileges()
    values = _click_signature.bind(*args, **kwargs)
    values.apply_defaults()
    options = values.arguments
    with _desktop_size_for_pyautogui():
        # Unity can miss a down/up pair delivered between rendered frames.
        # Hold each edge, including menu and tower clicks, on the guest desktop.
        if options['x'] is not None and options['y'] is not None:
            _real_move_to(options['x'], options['y'], duration=max(0.08, options['duration']), tween=options['tween'])
            _deliver_pointer_event()
        for index in range(options['clicks']):
            pyautogui.mouseDown(button=options['button'], _pause=False)
            try:
                time.sleep(0.12)
            finally:
                pyautogui.mouseUp(button=options['button'], _pause=False)
            if index + 1 < options['clicks']:
                time.sleep(max(0.08, options['interval']))
        if options.get('_pause', True):
            time.sleep(pyautogui.PAUSE)


def held_click(x, y, hold_seconds=0.12):
    """Hold across several game frames so Unity observes both button edges."""
    move_to(x, y)
    pyautogui.mouseDown(button='left')
    try:
        time.sleep(hold_seconds)
    finally:
        pyautogui.mouseUp(button='left')


def drag_to(*args, **kwargs):
    args, kwargs = _point_args(args, kwargs)
    with _desktop_size_for_pyautogui():
        return _real_drag_to(*args, **kwargs)


def screenshot(imageFilename=None, region=None):
    left, top, width, height = _client_with_recovery()
    game_width, game_height = ((1920, 1080) if width < 2240 else (2560, 1440))
    image = _real_screenshot(region=(left, top, width, height))
    if image.size != (game_width, game_height):
        from PIL import Image
        image = image.resize((game_width, game_height), Image.Resampling.BICUBIC)
    if region is not None:
        x, y, w, h = region
        image = image.crop((x, y, x + w, y + h))
    if imageFilename:
        image.save(imageFilename)
    return image


pyautogui.size = game_size
pyautogui.screenshot = screenshot
pyautogui.moveTo = move_to
pyautogui.click = click
pyautogui.dragTo = drag_to
