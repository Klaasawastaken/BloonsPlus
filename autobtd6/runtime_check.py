"""Read-only installer preflight. Never imports replay/helper or touches BTD6."""
import argparse
import importlib
from importlib import metadata
import json
from pathlib import Path
import sys


def check(requirements=None):
    errors = []
    if sys.version_info[:2] != (3, 12) or sys.maxsize <= 2**32:
        errors.append("Python 3.12 x64 is required")
    if requirements:
        for line in Path(requirements).read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "==" not in line:
                continue
            name, expected = line.split("==", 1)
            try:
                actual = metadata.version(name)
                if actual != expected:
                    errors.append(f"{name}: expected {expected}, found {actual}")
            except metadata.PackageNotFoundError:
                errors.append(f"Missing package: {name}")
    for module in ("numpy", "cv2", "PIL.Image", "tensorflow", "keras", "pyautogui", "keyboard", "ahk", "requests"):
        try:
            importlib.import_module(module)
        except Exception as error:
            errors.append(f"{module}: {type(error).__name__}: {error}")
    try:
        files = metadata.files("ahk-binary") or []
        if not any(str(file).lower().endswith("autohotkey.exe") and Path(file.locate()).is_file() for file in files):
            errors.append("AutoHotkey keyboard sender executable is missing")
    except metadata.PackageNotFoundError:
        errors.append("AutoHotkey keyboard sender package is missing")
    return {"ready": not errors, "python": sys.version.split()[0], "errors": errors}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements")
    result = check(parser.parse_args().requirements)
    print(json.dumps(result), flush=True)
    raise SystemExit(0 if result["ready"] else 1)
