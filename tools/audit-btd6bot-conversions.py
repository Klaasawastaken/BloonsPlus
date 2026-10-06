"""Read-only source preservation audit; never launch gameplay or rewrite routes."""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('route_import', ROOT / 'tools/import-public-routes.py')
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


def audit():
    sources = {}
    for source in sorted((ROOT / 'btd6bot/btd6bot/plans').glob('*.py')):
        identity = next(((source.stem[:-len(suffix)], values[0])
                         for suffix, values in importer.BTD6BOT_MODES.items()
                         if source.stem.endswith(suffix) and len(source.stem) > len(suffix)), None)
        if identity is None:
            continue
        slug = importer.map_slug(identity[0].replace('#', ''))
        if slug is None:
            continue
        try:
            route = importer.convert_btd6bot(source)
            verdict = dict(status='source-convertible' if not route.lossy else 'source-omissions',
                           omissions=sorted(route.lossy))
        except importer.Unsupported as error:
            verdict = dict(status='source-unsupported', reason=str(error))
        sources[(slug, identity[1])] = dict(verdict, source=source.relative_to(ROOT).as_posix(),
            sourceHash=hashlib.sha256(source.read_bytes()).hexdigest())
    findings = []
    for file in sorted((ROOT / 'autobtd6/playthroughs').glob('*#source_btd6bot*.btd6')):
        fields = file.stem.split('#')
        if len(fields) < 3:
            continue
        flags = fields[3:]
        source_mode = next((flag[len('from_'):] for flag in flags if flag.startswith('from_')), fields[1])
        if 'fromChimps' in flags:
            source_mode = 'chimps'
        elif 'fromImpoppable' in flags:
            source_mode = 'impoppable'
        verdict = sources.get((fields[0], source_mode), dict(status='source-unresolved'))
        findings.append(dict(verdict, file=file.name, map=fields[0], targetMode=fields[1],
            sourceMode=source_mode, compatibilityCopy='compat' in flags,
            routeHash=hashlib.sha256(file.read_bytes()).hexdigest()))
    return dict(scanned=len(findings), counts=dict(Counter(item['status'] for item in findings)),
        findings=findings,
        note='Convertible source is not proof that an existing route preserves it or wins. Unsupported source commands require review before legacy copies are admitted. No route rewritten; no gameplay launched.')


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
