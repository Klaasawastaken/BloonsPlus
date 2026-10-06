"""Read-only inventory of BloonsPlayer controls needing faithful replay support."""
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVISION = '17d624879c5ad777e82594da34450e66b2d60756'
SOURCE = f'https://github.com/piweiblen/BloonsPlayer/blob/{REVISION}/src/player.py'


def controls(text):
    result = []
    for number, raw in enumerate(text.splitlines(), 1):
        command = raw.split('#', 1)[0].strip().lower()
        if command.startswith('change speed'):
            kind, semantics = 'speed-toggle', 'One Space press; not an absolute fast/slow setting.'
        elif command.startswith('toggle autostart'):
            kind, semantics = 'autostart-toggle', 'Open pause settings, attempt detected on/off clicks in a three-iteration loop, close settings.'
        elif command.startswith('start round'):
            kind = 'round-start'
            # Pinned parse_args splits commas and strips parentheses/spaces.
            # TAS_start_round checks only its first argument for literal "slow".
            first_arg = command[len('start round'):].split(',')[0].strip('( )')
            semantics = 'One Space press.' if first_arg == 'slow' else 'Space, configured input delay, then Space again.'
        elif command.startswith('wait '):
            kind, semantics = 'unregistered-wait', 'No wait handler is registered in the pinned source; seconds interpretation needs strategy review.'
        else:
            continue
        result.append({'line': number, 'command': command, 'kind': kind, 'sourceBehavior': semantics})
    return result


def audit():
    spec = importlib.util.spec_from_file_location('public_route_import', ROOT / 'tools/import-public-routes.py')
    importer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(importer)
    folder = ROOT / 'route-library/public-sources/piweiblen-BloonsPlayer/tas'
    if not folder.is_dir():
        raise FileNotFoundError('Pinned BloonsPlayer TAS source directory is unavailable')
    findings, totals = [], Counter()
    files = sorted(folder.rglob('*.txt'))
    for file in files:
        operations = controls(file.read_text(encoding='utf-8-sig'))
        if not operations:
            continue
        entry = {'sourceFile': file.relative_to(ROOT).as_posix(), 'controls': operations}
        totals.update(item['kind'] for item in operations)
        try:
            route = importer.convert_bloonsplayer(file)
            entry.update(map=route.map, mode=route.mode, conversion='lossy' if route.lossy else 'complete',
                         remainingOmissions=sorted(route.lossy))
        except importer.Unsupported as error:
            entry.update(conversion='rejected', reason=str(error))
        findings.append(entry)
    return {'sourceImplementation': SOURCE, 'scanned': len(files), 'affected': len(findings),
            'operationCounts': dict(sorted(totals.items())), 'findings': findings,
            'requiredRuntimeWork': [
                'Establish observed initial autostart state; upstream ensure-autostart is a user preference.',
                'Serialize controls with placements, upgrade retries and delayed ability targeting.',
                'Prevent the automatic round controller from issuing competing Space presses.',
                'Observe and checkpoint a control before consuming it; do not repeat a toggle after resume.',
                'Restore normal victory/defeat observation without exiting when recorded controls end.',
            ],
            'note': 'Read-only audit. No recording regenerated, no gameplay launched, no route victory implied.'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
