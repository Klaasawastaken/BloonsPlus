"""Create the Bloons+ GPU virtual machine with App Sandbox and stage Steam + Bloons+ inside it.

BTD6 only reacts to the real mouse, so Bloons+ can't drive it in the background on this desktop.
Inside a VM it gets its own virtual mouse and keyboard, so the automation runs while this PC stays
free. Two callers share this script:
  * vm/setup-vm.cmd (developer shortcut; it elevates and starts the App Sandbox daemon first), and
  * vm-setup.js, the in-app Setup bar, which passes --appsandbox-dir/--iso/--installer/--cache-dir.
Re-running is safe: every step checks what is already done.

Actions:
  provision     (default) create or start the VM, install Steam + Bloons+ in it, create the
                BloonsPlusApp logon task, open Steam and the VM window for the user's sign-in.
  steam-install open Steam's own install prompt for Bloons TD 6 on the VM desktop again.
  launch-app    start Bloons+ inside the VM (runs the BloonsPlusApp logon task now).
Steam owns authentication: the user types their login and 2FA in Steam's window in the VM.
This script never asks for, stores or types Steam credentials.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VM_PREFIX = 'Bloons'
VM_NAMES = ['BloonsPlusVM2', 'BloonsPlusVM3', 'BloonsPlusVM4']
USER, PASSWORD = 'user', 'test123'   # App Sandbox defaults; the VM is NAT-only and unreachable from the network.
STEAM_SETUP_URL = 'https://cdn.cloudflare.steamstatic.com/client/installer/SteamSetup.exe'
STEAM_EXE = r'C:\Program Files (x86)\Steam\steam.exe'
GUEST_APP = r'C:\Users\%s\AppData\Local\Programs\Bloons+\Bloons+.exe' % USER
GUEST_INSTALL_RESULT = r'C:\Users\%s\AppData\Local\BloonsPlus\installer-result.txt' % USER
GUEST_INSTALL_LOCK = GUEST_APP.rsplit('\\', 1)[0] + r'\.bloons-install.lock'
BTD6_APP_ID = 960090


def released_installer():
    try:
        release = json.loads((ROOT / 'docs/release.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(release, dict):
        return None
    version = re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+-preview\.([0-9]+)', str(release.get('tag_name', '')))
    assets = release.get('assets')
    asset = next((item for item in assets if isinstance(item, dict) and item.get('name') == 'BloonsPlusSetup.exe'), None) if isinstance(assets, list) else None
    size = asset.get('size') if asset else None
    if not version or type(size) is not int or size <= 0 or size > 2**53 - 1:
        return None
    candidate = ROOT / 'dist' / ('preview' + version[1]) / 'BloonsPlusSetup.exe'
    try:
        actual_size = candidate.stat().st_size
    except FileNotFoundError:
        return None
    if not candidate.is_file() or actual_size != size:
        raise RuntimeError('The latest release installer is incomplete (size mismatch). Rebuild or download it before updating the VM.')
    return candidate


def default_installer():
    # A developer checkout builds dist/BloonsPlusSetup.exe; an installed Bloons+ keeps a copy of its
    # own installer next to Bloons+.exe (resources/app/vm -> install root).
    released = released_installer()
    if released:
        return released
    for candidate in (ROOT / 'dist' / 'BloonsPlusSetup.exe', ROOT.parent.parent / 'BloonsPlusSetup.exe'):
        if candidate.is_file():
            return candidate
    return ROOT / 'dist' / 'BloonsPlusSetup.exe'


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', nargs='?', default='provision', choices=['provision', 'steam-install', 'launch-app'])
    parser.add_argument('--appsandbox-dir', default=os.environ.get('APPSANDBOX_DIR', str(Path.home() / 'Downloads' / 'AppSandbox')))
    parser.add_argument('--iso', default=os.environ.get('BLOONS_VM_ISO'))
    parser.add_argument('--installer')
    parser.add_argument('--cache-dir', default=str(ROOT / 'dist'), help='where SteamSetup.exe is cached')
    parser.add_argument('--reinstall', action='store_true', help='copy and run the Bloons+ installer even if Bloons+ is already in the VM')
    args = parser.parse_args(argv)
    if args.installer is None and args.action == 'provision':
        args.installer = str(default_installer())
    args.appsandbox_dir = Path(args.appsandbox_dir)
    args.iso = Path(args.iso) if args.iso else args.appsandbox_dir / 'Win11_25H2_English_x64_v2.iso'
    args.installer = Path(args.installer) if args.installer else None
    args.cache_dir = Path(args.cache_dir)
    return args


def log(message):
    print(time.strftime('[%H:%M:%S] ') + message, flush=True)


def cached_steam_installer(target):
    """Reuse only a completed, unchanged download; never execute a partial cache."""
    target = Path(target)
    receipt = target.with_suffix('.download.json')
    try:
        metadata = json.loads(receipt.read_text(encoding='utf-8'))
        cached = target.read_bytes()
        if (metadata.get('url') == STEAM_SETUP_URL and cached.startswith(b'MZ')
                and metadata.get('size') == len(cached)
                and metadata.get('sha256') == hashlib.sha256(cached).hexdigest()):
            return target
    except (OSError, ValueError, AttributeError):
        pass
    target.parent.mkdir(parents=True, exist_ok=True)
    log('downloading Steam installer from the official Steam CDN')
    # Private temporary directory on the same volume makes replacement atomic.
    # The digest is a local cache-integrity receipt, not a publisher signature.
    with tempfile.TemporaryDirectory(prefix='steam-download-', dir=target.parent) as folder:
        partial = Path(folder) / 'SteamSetup.exe'
        with urllib.request.urlopen(STEAM_SETUP_URL, timeout=60) as response, partial.open('wb') as output:
            length = response.headers.get('Content-Length')
            expected = int(length) if length is not None else None
            written = 0
            while True:
                chunk = response.read(512 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                written += len(chunk)
        if expected is not None and written != expected:
            raise RuntimeError('Steam installer download incomplete; retry setup to download it again')
        payload = partial.read_bytes()
        if not payload.startswith(b'MZ') or len(payload) <= 2:
            raise RuntimeError('Steam download was not a Windows executable; retry setup')
        metadata = {'url': STEAM_SETUP_URL, 'size': written, 'sha256': hashlib.sha256(payload).hexdigest()}
        pending_receipt = Path(folder) / 'receipt.json'
        pending_receipt.write_text(json.dumps(metadata), encoding='utf-8')
        partial.replace(target)
        pending_receipt.replace(receipt)
    return target


def ssh_command(info):
    return ['ssh', '-i', asb.key_path(), '-p', str(info['port']), '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=NUL', '-o', 'IdentitiesOnly=yes',
            '-o', 'PreferredAuthentications=publickey', '-o', 'PasswordAuthentication=no',
            '-o', 'KbdInteractiveAuthentication=no', '-o', 'ConnectTimeout=15',
            '-o', 'BatchMode=yes', '-o', 'LogLevel=ERROR', '%s@127.0.0.1' % info['user']]


def ssh_key_access_error(detail):
    """Tell local key-file access failures apart from a guest rejecting the public key."""
    if 'Load key' in detail and ('Permission denied' in detail or 'Access is denied' in detail):
        return ('The Bloons+ setup process cannot read its App Sandbox SSH key (%s). '
                'Run setup as the Windows account that installed App Sandbox, or repair that '
                'account\'s read access to the key; the VM key itself was not rejected.' % asb.key_path())
    return None


def ssh(info, command, timeout=60):
    # OpenSSH may use cmd.exe or PowerShell as its guest shell. An encoded payload
    # preserves quotes, pipes and paths without an additional shell parsing them.
    encoded = base64.b64encode(command.encode('utf-16le')).decode('ascii')
    try:
        result = subprocess.run(ssh_command(info) + ['powershell -NoProfile -NonInteractive -EncodedCommand ' + encoded],
                                capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError('VM command timed out after %ss. The guest command may still be running; '
                           'check the VM before retrying setup. Command: %s' % (timeout, command)) from error
    if result.returncode != 0:
        detail = '\n'.join(value.strip() for value in (result.stderr, result.stdout) if value and value.strip())
        if not detail:
            detail = 'no diagnostic returned'
        local_key_error = ssh_key_access_error(detail)
        if local_key_error:
            raise RuntimeError(local_key_error + '\n' + detail)
        if 'Permission denied' in detail:
            raise RuntimeError('VM SSH key was rejected for %s@127.0.0.1:%s. The VM reports keyDeployed=%s, SSH state=%s. Recheck the selected App Sandbox key and VM key deployment.\n%s'
                               % (info.get('user', USER), info.get('port'), info.get('keyDeployed'), info.get('sshState'), detail))
        raise RuntimeError('VM command failed: %s\nssh exit %s: %s' % (command, result.returncode, detail))
    return result.stdout.strip()


def scp(info, source, target):
    result = subprocess.run(['scp', '-i', asb.key_path(), '-P', str(info['port']), '-o', 'StrictHostKeyChecking=no',
                             '-o', 'UserKnownHostsFile=NUL', '-o', 'IdentitiesOnly=yes',
                             '-o', 'PreferredAuthentications=publickey', '-o', 'PasswordAuthentication=no',
                             '-o', 'KbdInteractiveAuthentication=no', '-o', 'ConnectTimeout=15',
                             '-o', 'BatchMode=yes', '-o', 'LogLevel=ERROR',
                             str(source), '%s@127.0.0.1:%s' % (info['user'], target)], capture_output=True, text=True)
    if result.returncode:
        detail = result.stderr.strip()
        local_key_error = ssh_key_access_error(detail)
        if local_key_error:
            raise RuntimeError(local_key_error + '\n' + detail)
        if 'Permission denied' in detail:
            raise RuntimeError('VM SSH key was rejected during file copy to %s@127.0.0.1:%s (keyDeployed=%s, SSH state=%s). Check that Bloons+ is using the App Sandbox key for this VM.\n%s'
                               % (info.get('user', USER), info.get('port'), info.get('keyDeployed'), info.get('sshState'), detail))
        raise RuntimeError('VM file copy failed: %s' % (detail or 'scp exited with code %s' % result.returncode))


def stage_guest_installer(info, source):
    """Upload into a fresh application-owned folder and verify before execution."""
    source = Path(source)
    digest = hashlib.sha256()
    with source.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    size = source.stat().st_size
    directory = ssh(info, "$taskStaging = Join-Path $env:LOCALAPPDATA 'BloonsPlus\\updates\\%s'; "
                    "[IO.Directory]::CreateDirectory($taskStaging) | Out-Null; $taskStaging" % uuid.uuid4().hex)
    if not directory:
        raise RuntimeError('Could not create the VM update staging folder')
    target = directory.rstrip('\\/') + r'\BloonsPlusSetup.exe'
    scp(info, source, target.replace('\\', '/'))
    literal = target.replace("'", "''")
    verification = ssh(info, "$ErrorActionPreference='Stop'; $taskFile=Get-Item -LiteralPath '%s' -ErrorAction Stop; "
                       "$taskHash=Get-FileHash -LiteralPath '%s' -Algorithm SHA256 -ErrorAction Stop; "
                       "@{size=$taskFile.Length; sha256=$taskHash.Hash} | ConvertTo-Json -Compress" % (literal, literal), timeout=120)
    try:
        receipt = json.loads(verification)
        verified = receipt.get('size') == size and str(receipt.get('sha256', '')).lower() == digest.hexdigest()
    except (ValueError, AttributeError):
        verified = False
    if not verified:
        raise RuntimeError('VM installer verification failed; the uploaded file was not launched. Retry setup to copy it again.')
    log('VM installer upload verified (%d MB)' % (size // (1024 * 1024)))
    return target


def remove_staged_installer(info, target):
    # Remove only this attempt's file and empty directory; never recurse through updates.
    literal = target.replace("'", "''")
    try:
        ssh(info, "$ErrorActionPreference='Stop'; Remove-Item -LiteralPath '%s' -Force -ErrorAction Stop; "
            "Remove-Item -LiteralPath (Split-Path -Parent '%s') -ErrorAction Stop; 'OK'" % (literal, literal))
    except RuntimeError:
        log('Installation completed; the staged installer is still in use and was retained.')


def run_on_vm_desktop(info, task, program, arguments=''):
    # SSH sessions have no desktop; a one-off interactive task starts GUI programs in the signed-in session.
    # The guest's SSH shell is cmd.exe: the program path is wrapped in escaped double quotes.
    action = '\\"%s\\"%s' % (program, ' ' + arguments if arguments else '')
    subprocess.run(ssh_command(info) + ['schtasks /create /f /tn %s /sc once /st 00:00 /it /rl highest /tr "%s"' % (task, action)],
                   check=True, capture_output=True)
    subprocess.run(ssh_command(info) + ['schtasks /run /tn %s' % task], check=True, capture_output=True)


def guest_install_busy(info):
    """Probe native installer ownership without enumerating or stopping processes."""
    result = ssh(info, "$ErrorActionPreference='Stop'; $taskLock='%s'; "
                 "$taskFree=$true; if (Test-Path -LiteralPath $taskLock) { "
                 "try { $taskHandle=[IO.File]::Open($taskLock,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None); "
                 "$taskHandle.Dispose() } catch [IO.IOException] { "
                 "$taskCode=$_.Exception.HResult -band 65535; if ($taskCode -eq 32 -or $taskCode -eq 33) { $taskFree=$false } else { throw } } }; "
                 "if (!$taskFree) { 'BUSY' } else { "
                 "$taskRoot=Split-Path -Parent $taskLock; $taskPending=Join-Path $taskRoot '.bloons-setup\\owned-process.json'; "
                 "if (!(Test-Path -LiteralPath $taskPending)) { 'FREE' } else { try { "
                 "$taskAssembly=[Reflection.Assembly]::LoadFile((Join-Path $taskRoot 'BloonsPlusSetup.exe')); "
                 "$taskType=$taskAssembly.GetType('OwnedProcess'); "
                 "$taskConstructor=$taskType.GetConstructor([type[]]@([string],[Func[string]])); "
                 "$taskObserver=$taskConstructor.Invoke([object[]]@([string]$taskRoot,$null)); "
                 "$taskState=$taskType.GetMethod('Observe').Invoke($taskObserver,[object[]]@()); "
                 "if ($taskState -eq 'idle') { 'FREE' } elseif ($taskState -eq 'running') { 'BUSY' } else { 'UNKNOWN' } "
                 "} catch { 'UNKNOWN' } } }"
                 % GUEST_INSTALL_LOCK).strip()
    if result not in ('FREE', 'BUSY'):
        raise RuntimeError('Could not establish VM installer ownership; setup was not started.')
    return result == 'BUSY'


def guest_installer_matches(info, source):
    """A completed prior request can satisfy this update only for identical bytes."""
    digest = hashlib.sha256()
    with Path(source).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    target = GUEST_APP.rsplit('\\', 1)[0] + r'\BloonsPlusSetup.exe'
    result = ssh(info, "$ErrorActionPreference='Stop'; if (Test-Path -LiteralPath '%s') { "
                 "(Get-FileHash -LiteralPath '%s' -Algorithm SHA256 -ErrorAction Stop).Hash } else { 'MISSING' }"
                 % (target, target)).strip()
    return result.lower() == digest.hexdigest()


def supports_attempt_receipts(source):
    # Resources (including the app icon) can put CLR strings beyond 256 KiB.
    # Scan the bounded native stub, never strings inside its appended app ZIP.
    # This is a compatibility check; upload integrity is verified separately.
    marker = 'installer-result-'.encode('utf-16le')
    with Path(source).open('rb') as stream:
        size = stream.seek(0, os.SEEK_END)
        native_size = size
        if size >= 16:
            stream.seek(-16, os.SEEK_END)
            footer = stream.read(16)
            if footer[:8] == b'BLPZIP01':
                payload_size = int.from_bytes(footer[8:], 'little', signed=True)
                if payload_size <= 0 or payload_size >= size - 16:
                    return False
                native_size = size - 16 - payload_size
        stream.seek(0)
        remaining = min(native_size, 16 * 1024 * 1024)
        overlap = b''
        while remaining:
            chunk = stream.read(min(remaining, 64 * 1024))
            if not chunk:
                break
            combined = overlap + chunk
            if marker in combined:
                return True
            overlap = combined[-(len(marker) - 1):]
            remaining -= len(chunk)
        return False


def remove_guest_install_task(info, attempt):
    if not re.fullmatch(r'[a-f0-9]{32}', attempt):
        raise ValueError('Invalid installer attempt identifier')
    try:
        # Delete only this attempt's registration. schtasks /delete does not
        # interrupt the program, including after an install wait timed out.
        ssh(info, "& schtasks.exe /delete /tn 'BloonsPlusSetup-%s' /f; "
            "if ($LASTEXITCODE -ne 0) { throw 'Could not remove setup task registration' }" % attempt)
    except RuntimeError:
        log('The setup task registration was retained; installer processes were not stopped.')


def wait_for_guest_install(info, timeout=2700, attempt=None):
    """Do not report success just because Task Scheduler accepted the launch request."""
    result_path = GUEST_INSTALL_RESULT
    if attempt is not None:
        if not re.fullmatch(r'[a-f0-9]{32}', attempt):
            raise ValueError('Invalid installer attempt identifier')
        result_path = GUEST_INSTALL_RESULT.replace('installer-result.txt', 'installer-result-%s.txt' % attempt)
    deadline = time.time() + timeout
    next_report = time.time() + 30
    while time.time() < deadline:
        busy = guest_install_busy(info)
        result = ssh(info, "if (Test-Path '%s') { Get-Content -Raw '%s' } else { 'PENDING' }"
                     % (result_path, result_path)).strip()
        if result == 'OK' and not busy:
            log('Bloons+ installer confirmed completion in the VM')
            return
        if result.startswith('ERROR:') and not busy:
            raise RuntimeError('Bloons+ installer failed in the VM: %s' % result)
        if result.startswith('RESTART_REQUIRED:') and not busy:
            raise RuntimeError('Restart Windows inside the VM, then resume Bloons+ setup: %s' % result)
        if time.time() >= next_report:
            log('waiting for Bloons+ installer in the VM (%s)' % result[:80])
            next_report = time.time() + 30
        time.sleep(5)
    raise TimeoutError('Bloons+ installer did not confirm completion within 45 minutes. '
                       'Check the VM installer log in AppData\\Local\\BloonsPlus\\installer.log.')


def create_logon_task(info):
    # Bloons+ in the VM starts at every logon so the host's Setup bar reconnects on its own.
    action = '\\"%s\\"' % GUEST_APP
    subprocess.run(ssh_command(info) + ['schtasks /create /f /tn BloonsPlusApp /sc onlogon /it /rl highest /tr "%s"' % action],
                   check=True, capture_output=True)


def create_vm(client, iso):
    # App Sandbox can fail a build at its bcdboot step and then delete the VM (issue #62: remnants of a
    # failed build break the next one with the same name), so each retry uses a fresh name.
    for attempt, name in enumerate(VM_NAMES):
        code, body = client.create(name=name, osType='Windows', imagePath=str(iso), ramMb=16384, cpuCores=8, hddGb=120,
                                   gpuMode=1, networkMode=1, adminUser=USER, adminPass=PASSWORD,
                                   sshEnabled=True, sshDeployKey=True)
        if code not in (200, 202):
            sys.exit('VM create rejected: %s' % body.get('error'))
        log('creating %s: unattended Windows install, usually 15-20 minutes' % name)
        try:
            return client.wait_online(name, timeout=3600)
        except RuntimeError as error:
            if 'vanished' not in str(error) or attempt + 1 == len(VM_NAMES):
                raise
            log('App Sandbox dropped %s during its build; retrying under a new name in 30 s' % name)
            time.sleep(30)


def online_vm(client, iso, allow_create):
    existing = [vm['name'] for vm in client.list() if vm['name'].startswith(VM_PREFIX)]
    if existing:
        name = existing[0]
        if client.status(name)['state'] == 'stopped':
            log('starting %s' % name)
            client.start(name)
        return client.wait_online(name, timeout=3600)
    if not allow_create:
        sys.exit('No Bloons+ VM exists yet; run the full setup first.')
    if not iso.is_file():
        sys.exit('Windows 11 ISO not found: %s' % iso)
    return create_vm(client, iso)


def wait_ssh(client, name):
    deadline = time.time() + 600
    next_report = 0
    while True:
        info = client.ssh_info(name)
        if info.get('sshState') == 4 and info.get('keyDeployed') is True:
            return info
        if time.time() > deadline:
            sys.exit('SSH never became ready in the VM (state %s, key deployed %s)' % (info.get('sshState'), info.get('keyDeployed')))
        if time.time() >= next_report:
            log('VM online; waiting for SSH (state %s, key deployed %s, %ss remaining)' % (info.get('sshState'), info.get('keyDeployed'), int(deadline - time.time())))
            next_report = time.time() + 20
        time.sleep(5)


def open_display(client, name):
    deadline = time.time() + 300
    while not client.display_ready(name):
        if time.time() > deadline:
            log('the VM display is not ready yet; open it later from the Setup bar')
            return
        time.sleep(2)
    client.open_display(name)


def steam_install_prompt(info):
    # Steam's own URI handler asks the signed-in user to install BTD6. Started on the VM desktop:
    # a Start-Process from the SSH session would not reach the user's Steam.
    run_on_vm_desktop(info, 'BloonsPlusSteamInstall', STEAM_EXE, 'steam://install/%d' % BTD6_APP_ID)


def provision(client, args):
    if not args.installer.is_file():
        sys.exit('Bloons+ installer not found: %s' % args.installer)
    log('App Sandbox %s, host has %s GB free' % (client.version().get('version'), client.host().get('freeGb')))
    status = online_vm(client, args.iso, allow_create=True)
    name = status['name']
    log('VM %s online (%s MB RAM, %s cores, GPU mode %s)' % (name, status['ramMb'], status['cpuCores'], status['gpuMode']))
    info = wait_ssh(client, name)
    waited_for_installer = guest_install_busy(info)
    if waited_for_installer:
        log('an existing Bloons+ installer owns the VM installation; waiting for it to finish')
        wait_for_guest_install(info)
    desktop = ssh(info, '[Environment]::GetFolderPath(\'Desktop\')')

    if ssh(info, "Test-Path '%s'" % STEAM_EXE) != 'True':
        log('installing Steam in the VM')
        args.cache_dir.mkdir(parents=True, exist_ok=True)
        steam_setup = cached_steam_installer(args.cache_dir / 'SteamSetup.exe')
        scp(info, steam_setup, desktop.replace('\\', '/') + '/SteamSetup.exe')
        ssh(info, 'Start-Process -Wait \'%s\\SteamSetup.exe\' -ArgumentList \'/S\'' % desktop, timeout=600)

    installed = ssh(info, "Test-Path '%s'" % GUEST_APP) == 'True'
    needs_install = not installed or args.reinstall
    if installed and waited_for_installer and guest_installer_matches(info, args.installer):
        needs_install = False
        log('the existing installer completed this exact update; reusing the installation')
    if needs_install:
        if not supports_attempt_receipts(args.installer):
            raise RuntimeError('This older installer does not support isolated VM setup results. Download the latest Bloons+ installer before updating the VM.')
        log('copying the Bloons+ installer into the VM (%d MB)' % (args.installer.stat().st_size // (1024 * 1024)))
        guest_installer = stage_guest_installer(info, args.installer)
    log('creating the BloonsPlusApp logon task in the VM')
    create_logon_task(info)

    run_on_vm_desktop(info, 'BloonsPlusSteam', STEAM_EXE)
    if needs_install:
        # The native installer rechecks guest idleness before closing its owned
        # controller. Do not stop it here: gameplay may have started since the
        # host's earlier check, and a duplicate request may lose ownership.
        # An attempt-specific receipt cannot be cleared by another host request
        # or mistaken for an older installer result. The native lock still owns
        # the global compatibility receipt.
        attempt = uuid.uuid4().hex
        # The installer downloads Bloons+'s Python packages in the VM and then starts Bloons+.
        log('running the Bloons+ installer in the VM (it downloads its Python packages; this takes a while)')
        try:
            run_on_vm_desktop(info, 'BloonsPlusSetup-' + attempt, guest_installer, '/silent /attempt:' + attempt)
            wait_for_guest_install(info, attempt=attempt)
        finally:
            remove_guest_install_task(info, attempt)
        remove_staged_installer(info, guest_installer)
    else:
        subprocess.run(ssh_command(info) + ['schtasks /run /tn BloonsPlusApp'], capture_output=True)
    log('opening the official Steam install prompt for Bloons TD 6 (AppID %d)' % BTD6_APP_ID)
    steam_install_prompt(info)
    open_display(client, name)
    log('Steam is ready for sign-in. Enter your Steam login and any 2FA code in the Steam window in the VM.')
    log('After sign-in Steam installs Bloons TD 6 (run it fullscreen at 1920x1080).')


def main(argv=None):
    global asb
    args = parse_args(argv)
    sys.path.insert(0, str(args.appsandbox_dir / 'headless-api'))
    import asb  # noqa: E402  (App Sandbox's stdlib-only SDK)
    client = asb.connect()
    if args.action == 'provision':
        provision(client, args)
        return
    name = online_vm(client, args.iso, allow_create=False)['name']
    info = wait_ssh(client, name)
    if args.action == 'steam-install':
        run_on_vm_desktop(info, 'BloonsPlusSteam', STEAM_EXE)
        steam_install_prompt(info)
        open_display(client, name)
        log('Steam install prompt for Bloons TD 6 opened in the VM window.')
    elif args.action == 'launch-app':
        if guest_install_busy(info):
            log('waiting for the active VM installer before launching Bloons+')
            wait_for_guest_install(info)
        # Never start a second copy, and never start Bloons+ while its installer is still writing files.
        # Do not pass the '+' name through Get-Process -Name: PowerShell treats
        # it as a wildcard pattern in some guest builds and the SSH wrapper then
        # returns a non-zero command error. Enumerate processes and compare exact
        # names instead; an absent process is a normal state, not a setup failure.
        # The scheduled task is idempotent. Avoid a guest PowerShell process probe here: some
        # Windows guest shells reject even a harmless Get-Process pipeline over SSH, while the
        # task runner itself remains available and reports a useful status.
        launch_command = ssh_command(info) + ['schtasks /run /tn BloonsPlusApp']
        launch = subprocess.run(launch_command, capture_output=True, text=True)
        if launch.returncode:
            detail = (launch.stderr or launch.stdout or '').strip()
            # The scheduled task can be unavailable for a few seconds while the guest shell
            # finishes loading. Retry once, but preserve the real SSH/task error if it persists.
            time.sleep(3)
            launch = subprocess.run(launch_command, capture_output=True, text=True)
            if launch.returncode:
                detail = (launch.stderr or launch.stdout or detail).strip()
                raise RuntimeError('Could not start Bloons+ scheduled task in the VM (ssh exit %s): %s'
                                   % (launch.returncode, detail or 'no diagnostic returned'))
        log('started Bloons+ in the VM')


asb = None

if __name__ == '__main__':
    main()
