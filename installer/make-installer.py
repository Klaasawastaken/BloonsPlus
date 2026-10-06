"""Build the per-user Bloons+ online installer (dist/BloonsPlusSetup.exe) without external build tools.

Layout: C# bootstrap (installer-bootstrap.cs) + an appended zip payload + footer "BLPZIP01" + payload length.
The payload holds only what runs on the user's PC: the Electron runtime, the app, AutoBTD6 and a trimmed base
Python. Everything big from third parties is downloaded at setup time instead: pip packages (installer),
App Sandbox, the Windows 11 ISO (Fido) and Steam (the in-app Setup bar, vm-setup.js).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
STAGE = DIST / "installer-stage"
PACKAGE = DIST / "BloonsPlusPayload.zip"
OUTPUT = DIST / "BloonsPlusSetup.exe"
REQUIRED_RUNTIME_FILES = (
    "lib/vm-setup.js", "lib/automation.js", "lib/route-validation.js", "assets/app/setup-bar.js", "vm/setup-vm.py", "vm/iso-patch.exe", "autobtd6/runtime_check.py", "autobtd6/placement_hints.py", "data/tower-upgrades.json", "lib/support-report.js", "lib/live-screen.js", "assets/app/vm-viewer.js", "autobtd6/live_capture.py", "tools/read-hero-selection.js", "tools/verify-map-page.js", "python/Lib/ensurepip/__init__.py", "python/Lib/venv/__init__.py",
    'lib/setup-session.js', 'lib/setup-controller.js', 'assets/app/setup-client.js',
    'assets/app/startup.js', 'assets/app/startup.css', 'assets/app/brand-tokens.css', 'assets/logo.svg',
)

ELECTRON = ROOT / "node_modules" / "electron" / "dist"
PYVENV_CONFIG = ROOT / ".venv" / "pyvenv.cfg"
PYTHON_HOME = Path(next((line.split("=", 1)[1].strip() for line in PYVENV_CONFIG.read_text(encoding="utf-8").splitlines() if line.strip().lower().startswith("home =")), ""))

# The bundled app currently uses AutoBTD6. These two vendored engines are retained in
# the workspace for later work, but their source and documentation do not belong in the
# current installer payload (the V2/V3 tabs were removed from the product UI).
SKIP_DIRS = {".git", ".superpowers", ".bloons-setup", "setup-handoff", "setup-sessions", "__pycache__", ".cache", ".pytest_cache", ".mypy_cache", ".claude", ".codex", ".agents", "btd6autoplay", "btd6bot", "failure-shots", "public-sources", "obsolete-conversions", "unsupported-conversions", "copied-drafts", "copied-btd6bot-aliases", "broken-guide-routes", "tools", "private", "tests"}
PERSONAL_FILES = {"game-observations.json", "automation-progress.json", "game-state.json", "last-hero.json", "upgrade-memory.json", "route-checkpoint.json", "Profile.Save", "playthrough_stats.json", "experimental-ai-data.json", "route-failures.json", "route-verification.json", "route-strengthen-queue.json", "pending-automation.json", "live-frame.jpg", "live-frame.jpg.tmp", "viewer-request.json", "host.json", "pause.flag", "exit_after_game.flag"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp"}
# Base-Python parts never used at runtime: Tk GUI, IDLE, turtle demos, C headers/import libraries (every
# pinned pip package ships a wheel), the base's own pip launchers (the private venv has its own) and the
# CPython self-test modules. ensurepip and venv stay: setup creates the private venv from them.
PYTHON_EXCLUDES = {
    "Lib/site-packages", "Lib/test", "Lib/tkinter", "Lib/idlelib", "Lib/turtledemo", "Lib/turtle.py",
    "tcl", "include", "libs", "Scripts", "DLLs/_tkinter.pyd", "DLLs/tcl86t.dll", "DLLs/tk86t.dll",
    "DLLs/_ctypes_test.pyd", "DLLs/_testbuffer.pyd", "DLLs/_testcapi.pyd", "DLLs/_testclinic.pyd",
    "DLLs/_testconsole.pyd", "DLLs/_testimportmultiple.pyd", "DLLs/_testinternalcapi.pyd",
    "DLLs/_testmultiphase.pyd", "DLLs/_testsinglephase.pyd",
}
# tesseract.js in Node loads its cores with require() and each core reads its sibling .wasm file with fs;
# the base64-embedded *.wasm.js copies (17 MB) exist only for browsers.
TESSERACT_CORE_SKIP_SUFFIX = ".wasm.js"


def copy_tree(source: Path, target: Path, *, exclude_names: set[str] | None = None, exclude_relative_paths: set[str] | None = None) -> None:
    excluded = SKIP_DIRS | (exclude_names or set())
    excluded_paths = {Path(value) for value in (exclude_relative_paths or set())}
    for current, dirs, files in os.walk(source):
        relative = Path(current).relative_to(source)
        dirs[:] = sorted(name for name in dirs if name not in excluded and (relative / name) not in excluded_paths)
        out_dir = target / relative
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            src = Path(current) / name
            if name in PERSONAL_FILES or name.startswith((".env", "debug-", "id_appsandbox")) or src.suffix.lower() in SKIP_SUFFIXES | {".key", ".pem", ".save", ".pfx", ".p12"} or (relative / name) in excluded_paths:
                continue
            shutil.copy2(src, out_dir / name)


def runtime_node_packages() -> list[str]:
    """node_modules folders of the production dependency tree (package-lock marks dev-only ones)."""
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    return sorted(key for key, entry in lock["packages"].items() if key.startswith("node_modules/") and not entry.get("dev"))


def copy_node_modules(target: Path) -> None:
    # Only what pngjs and tesseract.js need at runtime. The electron npm package and its downloader
    # (@electron/get, got, global-agent, sumchecker, ...) are dev dependencies: Electron itself is
    # already the package root.
    for package in runtime_node_packages():
        source = ROOT / package
        if not source.is_dir():
            raise SystemExit(f"Missing runtime package {package}; run npm install")
        if package == "node_modules/tesseract.js-core":
            out = target / "tesseract.js-core"
            out.mkdir(parents=True, exist_ok=True)
            for file in source.iterdir():
                if file.is_file() and not file.name.endswith(TESSERACT_CORE_SKIP_SUFFIX):
                    shutil.copy2(file, out / file.name)
            continue
        copy_tree(source, target / Path(package).relative_to("node_modules"))


def optimize_pngs(folder: Path) -> None:
    """Losslessly re-encode AutoBTD6's PNG templates at maximum compression (pixels and mode are verified
    identical). Results are cached by content hash so rebuilds stay fast. Skipped without Pillow/numpy."""
    try:
        from PIL import Image
        import numpy
    except ImportError:
        print("Pillow/numpy not available; PNG templates are packed as-is", flush=True)
        return
    cache = DIST / "png-cache"
    cache.mkdir(parents=True, exist_ok=True)
    saved = 0
    for path in folder.rglob("*.png"):
        raw = path.read_bytes()
        cached = cache / (hashlib.sha1(raw).hexdigest() + ".png")
        if not cached.is_file():
            original = Image.open(io.BytesIO(raw))
            original.load()
            buffer = io.BytesIO()
            extra = {"transparency": original.info["transparency"]} if "transparency" in original.info else {}
            original.save(buffer, "PNG", optimize=True, **extra)
            candidate = buffer.getvalue()
            check = Image.open(io.BytesIO(candidate))
            identical = check.mode == original.mode and numpy.array_equal(numpy.asarray(check), numpy.asarray(original))
            cached.write_bytes(candidate if identical and len(candidate) < len(raw) else raw)
        optimized = cached.read_bytes()
        saved += len(raw) - len(optimized)
        path.write_bytes(optimized)
    print(f"PNG templates re-encoded losslessly: {saved / (1024**2):.1f} MiB saved", flush=True)


def stage_app() -> None:
    runpy.run_path(str(ROOT / 'installer/brand_tokens.py'))['generate']()
    if not ELECTRON.joinpath("electron.exe").is_file():
        raise SystemExit("Electron runtime not found at node_modules/electron/dist/electron.exe")
    if not PYTHON_HOME.joinpath("python.exe").is_file():
        raise SystemExit(f"Python base runtime not found: {PYTHON_HOME}")

    if STAGE.exists():
        shutil.rmtree(STAGE)
    app = STAGE / "resources" / "app"
    app.mkdir(parents=True)

    # Electron's unpacked runtime goes at installer-root; its application lives at
    # resources/app so the stock Electron executable can launch electron-main.js.
    for item in ELECTRON.iterdir():
        if item.name == "electron.exe":
            shutil.copy2(item, STAGE / "Bloons+.exe")
        elif item.name == "resources":
            # default_app.asar is Electron's demo app; Bloons+ ships resources/app instead.
            copy_tree(item, STAGE / "resources", exclude_relative_paths={"default_app.asar"})
        elif item.name == "locales" and item.is_dir():
            # Bloons+ has no locale switcher; keep the Chromium English pack only.
            locale_target = STAGE / "locales"
            locale_target.mkdir(parents=True, exist_ok=True)
            english = item / "en-US.pak"
            if english.is_file():
                shutil.copy2(english, locale_target / english.name)
        elif item.is_dir():
            copy_tree(item, STAGE / item.name)
        else:
            shutil.copy2(item, STAGE / item.name)

    for item in ROOT.iterdir():
        if item.name in PERSONAL_FILES:
            continue
        if item.name in {".venv", "node_modules", ".git", "dist", "__pycache__", "installer", "make-installer.ps1", "install-bloons-plus.ps1", "install-bloons-plus.cmd", "TODO.md"}:
            continue
        if item.is_file() and item.suffix.lower() in {".js", ".html", ".css", ".json", ".md", ".txt", ".ico"}:
            if item.name.lower().startswith("debug-"):
                continue
            shutil.copy2(item, app / item.name)
        elif item.is_dir() and item.name not in SKIP_DIRS:
            copy_tree(item, app / item.name)

    # Ship neutral account defaults; existing installations restore their own config.
    subprocess.run([sys.executable, str(ROOT / 'tools' / 'embed-exe-icon.py'),
                    str(STAGE / 'Bloons+.exe'), str(ROOT / 'bloonsplus.ico')], check=True)
    config_path = app / 'autobtd6' / 'userconfig.json'
    if not config_path.exists():
        shutil.copy2(app / 'autobtd6' / 'userconfig.example.json', config_path)
    config = json.loads(config_path.read_text(encoding='utf-8'))
    for section in ('monkey_knowledge', 'heros', 'unlocked_maps'):
        config[section] = {key: False for key in config.get(section, {})}
    config.setdefault('unlocked_maps', {})['monkey_meadow'] = True
    config['medals'] = {}
    config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
    optimize_pngs(app / "autobtd6" / "images")
    copy_node_modules(app / "node_modules")
    # Replay launches these helpers through Node at runtime. Keep the build and
    # migration utilities out of the payload, but always ship the two visual
    # readers even though the repository-level tools directory is excluded.
    runtime_tools = app / "tools"
    runtime_tools.mkdir(parents=True, exist_ok=True)
    for name in ("read-hero-selection.js", "verify-map-page.js"):
        shutil.copy2(ROOT / "tools" / name, runtime_tools / name)
    # The base Python only bootstraps the private venv (setup downloads the pinned pip packages).
    copy_tree(PYTHON_HOME, app / "python", exclude_relative_paths=PYTHON_EXCLUDES)
    for required in REQUIRED_RUNTIME_FILES:
        if not (app / required).is_file():
            raise SystemExit(f"Staged app is missing {required}")


def write_inventory(stage: Path) -> None:
    files = []
    preserved = {'userconfig.json', 'automation-progress.json', 'game-observations.json', 'route-verification.json', 'playthrough_stats.json'}
    for file in sorted(stage.rglob('*')):
        if not file.is_file() or file.name == 'bloons-package.json':
            continue
        relative = file.relative_to(stage).as_posix()
        if file.name in preserved or any(part in relative.split('/') for part in ('route-library', 'playthroughs')) or '/data/config/' in '/' + relative:
            continue
        files.append({'path': relative, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    fingerprint = hashlib.sha256(json.dumps(files, separators=(',', ':')).encode()).hexdigest()
    package = json.loads((stage / 'resources/app/package.json').read_text(encoding='utf-8'))
    text = json.dumps({'protocolVersion': 1, 'version': package['version'], 'fingerprint': fingerprint, 'files': files}, separators=(',', ':'))
    if len(files) > 20000 or len(text.encode('utf-8')) > 8 * 1024 * 1024:
        raise ValueError('App inventory exceeds native safety limits')
    (stage / 'bloons-package.json').write_text(text, encoding='utf-8')


def zip_payload() -> None:
    write_inventory(STAGE)
    if PACKAGE.exists():
        PACKAGE.unlink()
    files = [path for path in STAGE.rglob("*") if path.is_file()]
    total = len(files)
    started = time.monotonic()
    with zipfile.ZipFile(PACKAGE, "w", allowZip64=True) as archive:
        for index, path in enumerate(files, 1):
            relative = path.relative_to(STAGE).as_posix()
            # Deflate at the maximum level is the best method the installer's System.IO.Compression reads.
            archive.write(path, relative, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            if index % 2500 == 0 or index == total:
                size = PACKAGE.stat().st_size if PACKAGE.exists() else 0
                print(f"Archived {index:,}/{total:,} files ({size / (1024**3):.2f} GiB)", flush=True)
    print(f"Payload ready: {PACKAGE} ({PACKAGE.stat().st_size / (1024**3):.2f} GiB) in {time.monotonic() - started:.0f}s", flush=True)


def build_installer() -> None:
    runpy.run_path(str(ROOT / 'installer/brand_tokens.py'))['generate']()
    compiler = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe"
    if not compiler.is_file():
        compiler = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET" / "Framework" / "v4.0.30319" / "csc.exe"
    if not compiler.is_file():
        raise SystemExit("The Windows .NET Framework C# compiler (csc.exe) is required to build the installer")
    source_directory = Path(__file__).resolve().parent
    sources = [source_directory / "installer-bootstrap.cs", *sorted((source_directory / "native").glob("*.cs")),
               *sorted((source_directory / "presentation").glob("*.cs"))]
    bootstrap = DIST / "BloonsPlusSetup.bootstrap.exe"
    inventory = STAGE / 'bloons-package.json'
    resources = ["/resource:" + str(inventory) + ",BloonsPlus.Package"] if inventory.is_file() else []
    subprocess.run([
        str(compiler), "/nologo", "/target:winexe", "/platform:x64", "/optimize+",
        "/reference:System.Windows.Forms.dll", "/reference:System.Drawing.dll",
        "/reference:System.IO.Compression.dll", "/reference:Microsoft.CSharp.dll",
        "/reference:System.Web.Extensions.dll",
        "/win32icon:" + str(ROOT / "bloonsplus.ico"),
        "/resource:" + str(ROOT / "tower-icons/engineer-monkey.png") + ",BloonsPlus.Engineer",
        "/out:" + str(bootstrap), *resources, *(str(source) for source in sources),
    ], check=True)
    for stale in (DIST / "BloonsPlusSetup.sed", DIST / "~BloonsPlusSetup.DDF", DIST / "~BloonsPlusSetup.CAB"):
        if stale.exists():
            stale.unlink()
    # Keep the last usable installer until every byte of its replacement is
    # written. A failed copy or locked destination must not publish a partial EXE.
    descriptor, temporary_name = tempfile.mkstemp(dir=OUTPUT.parent, prefix=OUTPUT.name + '.', suffix='.tmp')
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, 'wb') as installer, bootstrap.open("rb") as stub, PACKAGE.open("rb") as payload:
            shutil.copyfileobj(stub, installer, 1024 * 1024)
            payload.seek(0, os.SEEK_END)
            payload_length = payload.tell()
            payload.seek(0)
            shutil.copyfileobj(payload, installer, 4 * 1024 * 1024)
            installer.write(b"BLPZIP01")
            installer.write(payload_length.to_bytes(8, "little", signed=True))
            installer.flush()
            os.fsync(installer.fileno())
        os.replace(temporary, OUTPUT)
    finally:
        temporary.unlink(missing_ok=True)
    if not OUTPUT.is_file():
        raise SystemExit("Installer executable was not produced")
    print(f"Online installer ready: {OUTPUT} ({OUTPUT.stat().st_size / (1024**2):.1f} MiB). Python packages, App Sandbox, Windows 11 and Steam download during setup.")


if __name__ == "__main__":
    DIST.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(ROOT / "tools/check-publication.py")], check=True)
    stage_app()
    zip_payload()
    subprocess.run([sys.executable, str(ROOT / "tools/check-publication.py"), "--payload", str(PACKAGE)], check=True)
    build_installer()
