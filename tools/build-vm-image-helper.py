"""Build App Sandbox's MIT helper with the bounded guest boot fallback.

Run from a VS x64 developer command prompt with --source pointing to the
AppSandbox 0.1.9 tools/iso-patch source directory. No upstream files are changed.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NATIVE = r'''
/* BloonsPlus: embedded repair, exclusively for a new guest disk after exit 183. */
static int repair_guest_boot(const wchar_t *win, const wchar_t *efi,
                             const wchar_t *disk, DWORD number)
{
    HMODULE module = GetModuleHandleW(NULL);
    HRSRC resource = FindResourceW(module, MAKEINTRESOURCEW(701), RT_RCDATA);
    HGLOBAL loaded;
    const void *bytes;
    DWORD size, written;
    wchar_t temporary[MAX_PATH], folder[MAX_PATH], file[MAX_PATH], system[MAX_PATH], command[4096];
    GUID id;
    HANDLE output;
    int result = -1;
    if (!resource || !(loaded = LoadResource(module, resource)) ||
        !(bytes = LockResource(loaded)) || !(size = SizeofResource(module, resource))) return -1;
    if (!GetTempPathW(MAX_PATH, temporary) || CoCreateGuid(&id) != S_OK) return -1;
    swprintf_s(folder, MAX_PATH, L"%sbloons-boot-%08lx-%04x-%04x-%02x%02x%02x%02x%02x%02x%02x%02x",
        temporary, id.Data1, id.Data2, id.Data3, id.Data4[0], id.Data4[1], id.Data4[2], id.Data4[3],
        id.Data4[4], id.Data4[5], id.Data4[6], id.Data4[7]);
    if (!CreateDirectoryW(folder, NULL)) return -1;
    swprintf_s(file, MAX_PATH, L"%s\\repair.ps1", folder);
    output = CreateFileW(file, GENERIC_WRITE, 0, NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
    if (output == INVALID_HANDLE_VALUE) { RemoveDirectoryW(folder); return -1; }
    if (!WriteFile(output, bytes, size, &written, NULL) || written != size) {
        CloseHandle(output); DeleteFileW(file); RemoveDirectoryW(folder); return -1;
    }
    CloseHandle(output);
    if (GetSystemDirectoryW(system, MAX_PATH)) {
        /* Mounted roots end in a slash; a dot avoids Windows argument quoting ambiguity. */
        swprintf_s(command, 4096,
            L"\"%s\\WindowsPowerShell\\v1.0\\powershell.exe\" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File \"%s\" -WindowsRoot \"%s.\" -EfiRoot \"%s.\" -DiskFile \"%s\" -DiskNumber %lu",
            system, file, win, efi, disk, number);
        result = run_command(command, FALSE);
    }
    DeleteFileW(file); RemoveDirectoryW(folder);
    return result;
}

'''

BOOT = r'''
    /* ---- Step 10: Set up UEFI boot files with bcdboot ---- */
    log_msg(L"Installing boot files...");
    {
        wchar_t windows_dir[MAX_PATH], efi_clean[MAX_PATH], command[2048], system[MAX_PATH];
        wchar_t log_path[MAX_PATH], program_data[MAX_PATH];
        static const wchar_t *variants[] = { L"/v", L"/v /l en-us", L"/v /offline", L"/v /l en-us /offline" };
        int ret = -1, boot_ret, v;
        GetSystemDirectoryW(system, MAX_PATH);
        swprintf_s(windows_dir, MAX_PATH, L"%sWindows", win_mount);
        wcscpy_s(efi_clean, MAX_PATH, efi_mount);
        if (wcslen(efi_clean) && efi_clean[wcslen(efi_clean)-1] == L'\\') efi_clean[wcslen(efi_clean)-1] = 0;
        if (!GetEnvironmentVariableW(L"ProgramData", program_data, MAX_PATH)) wcscpy_s(program_data, MAX_PATH, L"C:\\ProgramData");
        swprintf_s(log_path, MAX_PATH, L"%s\\AppSandbox\\bcdboot.log", program_data);
        for (v=0; v<4 && ret!=0; v++) {
            swprintf_s(command, 2048,
                L"\"%s\\cmd.exe\" /c \"\"%s\\bcdboot.exe\" \"%s\" /s \"%s\" /f UEFI %s >>\"%s\" 2>&1\"",
                system, system, windows_dir, efi_clean, variants[v], log_path);
            ret=run_command(command, TRUE);
            log_msg(L"bcdboot attempt %d (%s) exit code %d", v+1, variants[v], ret);
        }
        boot_ret=ret;
        if (ret == 183) {
            log_msg(L"Recovering the new guest's UEFI boot store...");
            ret=repair_guest_boot(win_mount, efi_mount, vhdx_path, disk_number);
            log_msg(L"Guest boot-store recovery exit code %d", ret);
        }
        /* Preserve the existing controller's exact fail-fast diagnostic contract. */
        if (ret != 0) { log_err(L"Failed to install boot files (bcdboot exit code %d)", boot_ret); goto cleanup; }
    }

'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'vm' / 'iso-patch.exe')
    args = parser.parse_args()
    source = args.source.resolve()
    if not (source / 'iso-patch.c').is_file():
        parser.error('AppSandbox 0.1.9 iso-patch source is required')
    scratch = ROOT / '.superpowers'
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='image-helper-', dir=scratch) as temporary:
        build = Path(temporary)
        for path in source.rglob('*'):
            if path.is_file() and path.suffix in ('.c', '.h'):
                target = build / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        text = (build / 'iso-patch.c').read_text(encoding='utf-8-sig')
        start = text.index('    /* ---- Step 10: Set up UEFI boot files with bcdboot ---- */')
        end = text.index('    log_done(vhdx_path);', start)
        text = text[:start] + BOOT + text[end:]
        insertion = text.index('static int do_to_vhdx(')
        text = text[:insertion] + NATIVE + text[insertion:]
        (build / 'iso-patch.c').write_text(text, encoding='utf-8')
        shutil.copyfile(ROOT / 'vm' / 'boot-store-repair.ps1', build / 'boot-store-repair.ps1')
        (build / 'repair.rc').write_text('701 RCDATA "boot-store-repair.ps1"\n', encoding='ascii')
        subprocess.run(['rc.exe', '/nologo', '/fo', 'repair.res', 'repair.rc'], cwd=build, check=True)
        sources = ['iso-patch.c', 'ubuntu_vhdx.c', 'prefetch_build_deps.c', 'prefetch_wsl_deps.c',
                   'prefetch_repo.c', 'engine/log.c', 'engine/ext4.c', 'engine/squashfs.c',
                   'engine/xz/xz_dec_stream.c', 'engine/xz/xz_dec_lzma2.c', 'engine/xz/xz_dec_bcj.c',
                   'engine/xz/xz_crc32.c', 'engine/xz/xz_crc64.c']
        subprocess.run(['cl.exe', '/nologo', '/O1', '/MT', '/DWIN32', '/DNDEBUG', '/D_CONSOLE',
                        '/DUNICODE', '/D_UNICODE', '/D_CRT_SECURE_NO_WARNINGS', '/Fe:iso-patch.exe',
                        *sources, 'repair.res', '/link', 'advapi32.lib', '/DEBUG:NONE', '/INCREMENTAL:NO'],
                       cwd=build, check=True)
        # Only a successfully linked build replaces the bundled helper.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(build / 'iso-patch.exe', args.output)
    print('Built the native guest image helper with embedded boot repair.')


if __name__ == '__main__':
    main()
