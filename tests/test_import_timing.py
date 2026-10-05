import ast
import importlib.util
from pathlib import Path
import unittest
import tempfile
import io
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('import_timing', ROOT / 'tools/import-public-routes.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TimingConversionTests(unittest.TestCase):
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

    def test_zero_wait_is_a_noop(self):
        for command in ('wait()', 'wait(0)', 'wait(timer=0)'):
            route = module.Route('test', 'test', 'logs', 'hard')
            module.btd6bot_statement(route, ast.parse(command).body[0])
            self.assertFalse(route.lossy)


if __name__ == '__main__':
    unittest.main()
