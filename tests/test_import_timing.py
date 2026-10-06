import ast
import importlib.util
from pathlib import Path
import unittest
import tempfile
import io
from contextlib import redirect_stdout, ExitStack
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('import_timing', ROOT / 'tools/import-public-routes.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TimingConversionTests(unittest.TestCase):
    def test_randy_start_is_flow_control_and_finish_is_source_noop(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'logs_script.py'
            path.write_text("script = [Action('start', action='start', cost=0), Action('finish', action='finish', cost=0)]", encoding='utf-8')
            route = module.convert_randyhodges(path)
        self.assertIn('explicit start game / speed control', route.lossy)
        self.assertEqual(route.harmless, {'finish (automatic source handler sends no input)'})

    def test_full_import_preserves_repaired_generator_recording(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / 'playthroughs'
            output.mkdir()
            library = root / 'library'
            (library / 'metadata').mkdir(parents=True)
            original = output / 'logs#chimps#1920x1080#converted.btd6'
            content = b'# generator: import-public-routes.py\n# repaired after import\nround 6\n'
            original.write_bytes(content)
            def unsupported(path):
                raise module.Unsupported('offline fixture: no conversion')
            with ExitStack() as stack, redirect_stdout(io.StringIO()):
                stack.enter_context(patch.object(module, 'PT', output))
                stack.enter_context(patch.object(module, 'LIB', library))
                stack.enter_context(patch.object(module, 'compat_copies', return_value=[]))
                stack.enter_context(patch.object(module, 'validate', return_value={}))
                for name in ('convert_btd6bot', 'convert_bloonsplayer', 'convert_everythingmacro', 'convert_randyhodges'):
                    stack.enter_context(patch.object(module, name, unsupported))
                module.main()
                module.main()  # Repeating a batch must also preserve the same bytes.
                with patch.object(module, 'validate', return_value={original.name: 'invalid'}):
                    with self.assertRaisesRegex(ValueError, 'outside this import batch'):
                        module.main()
            self.assertTrue(original.exists())
            self.assertEqual(original.read_bytes(), content)

    def test_timing_candidates_preserve_existing_files_and_are_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            original = output / 'original#chimps#1920x1080.btd6'
            original.write_text('keep original recording', encoding='utf-8')
            with patch.object(module, 'PT', output), redirect_stdout(io.StringIO()):
                module.emit_timing_candidates()
                before = {p.name:p.read_bytes() for p in output.glob('*.btd6')}
                self.assertGreater(len(before), 1)
                module.emit_timing_candidates()
                self.assertEqual(before, {p.name:p.read_bytes() for p in output.glob('*.btd6')})
                self.assertEqual(original.read_text(encoding='utf-8'), 'keep original recording')
                candidate = next(output.glob('*#timing-preserved.btd6'))
                candidate.write_text('user edit', encoding='utf-8')
                with self.assertRaisesRegex(RuntimeError, 'Refusing to overwrite'):
                    module.emit_timing_candidates()
                self.assertEqual(candidate.read_text(encoding='utf-8'), 'user edit')

    def test_timing_and_manual_round_controls_are_not_harmless(self):
        for command in ('change_autostart()', 'end_round()', 'forward(1)', 'move_cursor(0.5, 0.5)'):
            with self.subTest(command=command):
                route = module.Route('test', 'test', 'logs', 'hard')
                module.btd6bot_statement(route, ast.parse(command).body[0])
                self.assertTrue(route.lossy, command)
                self.assertFalse(route.harmless)

    def test_wait_duration_is_preserved(self):
        for command, expected in (('wait(5)', 'wait 5 seconds'), ('wait(timer=1.5)', 'wait 1.5 seconds')):
            route = module.Route('test', 'test', 'logs', 'hard')
            module.btd6bot_statement(route, ast.parse(command).body[0])
            self.assertEqual(route.lines, [expected])
            self.assertFalse(route.lossy)

    def test_bloonsplayer_omitted_flow_is_not_harmless(self):
        for command in ('wait 2', 'lives 50', 'toggle autostart', 'start round turbo'):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'strategy.txt'
                path.write_text('open Logs, Hard, Standard\n' + command + '\n', encoding='utf-8')
                route = module.convert_bloonsplayer(path)
                self.assertTrue(route.lossy, command)
                self.assertFalse(route.harmless)

    def test_bloonsplayer_startup_intent_and_repeated_starts(self):
        for command, speed in [('start round', 'fast'), ('start round slow', 'slow')]:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'strategy.txt'
                path.write_text('open Logs, Hard, Standard\n' + command + '\n', encoding='utf-8')
                route = module.convert_bloonsplayer(path)
                self.assertEqual(route.lines, ['start round ' + speed])
                self.assertFalse(route.lossy)
                path.write_text('open Logs, Hard, Standard\n' + command + '\n' + command + '\n', encoding='utf-8')
                self.assertTrue(module.convert_bloonsplayer(path).lossy)

    def test_relative_speed_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'strategy.txt'
            path.write_text('open Logs, Hard, Standard\nchange speed\nchange speed\n', encoding='utf-8')
            route = module.convert_bloonsplayer(path)
            self.assertEqual(route.lines, ['change speed', 'change speed'])
            self.assertFalse(route.lossy)

    def test_speed_candidates_are_separate_idempotent_and_preserve_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            original = output / 'original#chimps#1920x1080.btd6'
            original.write_bytes(b'keep original recording\n')
            with patch.object(module, 'PT', output), patch.object(module, 'validate', return_value={}), redirect_stdout(io.StringIO()):
                module.emit_speed_candidates()
                before = {p.name:p.read_bytes() for p in output.glob('*.btd6')}
                self.assertEqual(len(before), 3)
                module.emit_speed_candidates()
                self.assertEqual(before, {p.name:p.read_bytes() for p in output.glob('*.btd6')})
                candidate = next(output.glob('*#speed-preserved.btd6'))
                candidate.write_text('user edit', encoding='utf-8')
                with self.assertRaisesRegex(RuntimeError, 'Refusing to overwrite'):
                    module.emit_speed_candidates()
                self.assertEqual(candidate.read_text(), 'user edit')
            self.assertEqual(original.read_bytes(), b'keep original recording\n')

    def test_bloonsplayer_delay_preserved_and_wait_assumption_explicit(self):
        for command, expected, review in [('delay 5', 'wait 5 seconds', False), ('wait 2', 'wait 2 seconds', True)]:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'strategy.txt'
                path.write_text('open Logs, Hard, Standard\n' + command + '\n', encoding='utf-8')
                route = module.convert_bloonsplayer(path)
                self.assertEqual(route.lines, [expected])
                self.assertEqual(bool(route.lossy), review)
                if review:
                    self.assertTrue(any('no pinned source handler' in item for item in route.lossy))

    def test_bloonsplayer_zero_delay_is_a_noop(self):
        for command in ('wait 0', 'delay 0.0'):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'strategy.txt'
                path.write_text('open Logs, Hard, Standard\n' + command + '\n', encoding='utf-8')
                route = module.convert_bloonsplayer(path)
                self.assertFalse(route.lossy)
                self.assertTrue(route.harmless)

    def test_everythingmacro_mid_round_delay_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'Maps' / 'Logs.ahk'
            path.parent.mkdir()
            path.write_text('RunConfig := {map: "Logs", difficulty: "Hard", gameMode: "Standard"}\n'
                            'TowerSetup := {}\nstrategy := [[20, 5000, () => UseAbility("1")]]', encoding='utf-8')
            route = module.convert_everythingmacro(path)
            self.assertFalse(route.lossy)
            self.assertFalse(route.harmless)
            self.assertEqual(route.lines, ['round 20 after 5 seconds', 'ability 1'])

    def test_legacy_audit_is_read_only_and_distinguishes_source_noops(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            bodies = {'logs#chimps#1920x1080#converted#lossy.btd6': '# dropped (timing only): wait(); start\nround 5\n',
                      'logs#chimps#1920x1080#timing-preserved.btd6': 'wait 5 seconds\n',
                      'logs#easy#1920x1080.btd6': '# dropped (timing only): bare name reference (no-op in source)\n'}
            for name, content in bodies.items():
                (directory / name).write_text(content, encoding='utf-8')
            before = {p.name: p.read_bytes() for p in directory.iterdir()}
            with patch.object(module, 'PT', directory):
                report = module.audit_legacy_timing()
            self.assertEqual(report['affected'], 1)
            self.assertEqual(report['findings'][0]['omitted'], ['wait()', 'start'])
            self.assertTrue(report['findings'][0]['timingAlternativePresent'])
            self.assertTrue(report['findings'][0]['lossyFlag'])
            self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})

    def test_zero_wait_is_a_noop(self):
        for command in ('wait()', 'wait(0)', 'wait(timer=0)'):
            route = module.Route('test', 'test', 'logs', 'hard')
            module.btd6bot_statement(route, ast.parse(command).body[0])
            self.assertFalse(route.lossy)


if __name__ == '__main__':
    unittest.main()
