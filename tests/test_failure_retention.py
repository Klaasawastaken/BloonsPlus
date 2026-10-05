"""Screenshot rotation must not erase structured failure history."""
import ast
import os
from pathlib import Path
import tempfile
import time
import unittest
from types import SimpleNamespace


class FailureRetention(unittest.TestCase):
    def test_failed_image_write_is_not_reported_as_saved(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'saveFailureShots')
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1], prefix='debug-retention-') as directory:
            logs = []
            env = dict(os=os, time=time, FAILURE_SHOT_DIR=directory, FAILURE_SHOTS_KEPT=60,
                       cv2=SimpleNamespace(imwrite=lambda *_: False), customPrint=logs.append)
            exec(compile(ast.Module(body=[function], type_ignores=[]), '<retention>', 'exec'), env)
            env['saveFailureShots']({'map': 'test', 'gamemode': 'hard'}, object(), object())
            self.assertFalse(any(line.startswith('FAILURE_SHOT ') for line in logs))
            self.assertTrue(any('could not save' in line for line in logs))

    def test_metadata_survives_image_rotation(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'saveFailureShots')
        workspace = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=workspace, prefix='debug-retention-') as directory:
            self.assertEqual(Path(directory).resolve().parent, workspace)
            for i in range(65):
                Path(directory, f'upgrade-{i}.json').write_text('{"status":"unselected"}')
                Path(directory, f'upgrade-{i}.png').write_bytes(b'old-frame')
            def write_image(name, frame):
                Path(name).write_bytes(b'new-frame')
                return True
            env = dict(os=os, time=time, FAILURE_SHOT_DIR=directory, FAILURE_SHOTS_KEPT=60,
                       cv2=SimpleNamespace(imwrite=write_image), customPrint=lambda *_: None)
            exec(compile(ast.Module(body=[function], type_ignores=[]), '<retention>', 'exec'), env)
            env['saveFailureShots']({'map': 'test', 'gamemode': 'hard'}, object(), object())
            self.assertEqual(len(list(Path(directory).glob('*.json'))), 65)
            self.assertEqual(len(list(Path(directory).glob('*.png'))), 60)


if __name__ == '__main__':
    unittest.main()
