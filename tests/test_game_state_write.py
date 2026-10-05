"""Exercise persistence without loading game input or touching live state."""
import ast
import json
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class GameStateWrite(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.target = Path(self.directory.name) / 'game-state.json'
        self.target.write_text('{"round": 10}', encoding='utf-8')
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'saveGameState')
        self.logs, self.waits = [], []
        env = dict(os=os, json=json, tempfile=tempfile,
                   time=SimpleNamespace(sleep=self.waits.append), customPrint=self.logs.append,
                   GAME_STATE_FILE=str(self.target), _game_state_lock=threading.Lock())
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<saveGameState>', 'exec'), env)
        self.save = env['saveGameState']

    def test_failed_replace_preserves_previous_state_and_cleans_temp(self):
        with patch.object(os, 'replace', side_effect=PermissionError('locked')) as replace:
            self.save(SimpleNamespace(to_dict=lambda: {'round': 11}))
        self.assertEqual(json.loads(self.target.read_text()), {'round': 10})
        self.assertEqual(replace.call_count, 5)
        self.assertEqual(len(self.waits), 4)
        self.assertEqual(list(self.target.parent.iterdir()), [self.target])
        self.assertEqual(len(self.logs), 1)

    def test_transient_lock_retries_same_payload(self):
        original = os.replace
        calls = []
        def replace(source, dest):
            calls.append(source)
            if len(calls) < 3:
                raise PermissionError('locked')
            return original(source, dest)
        with patch.object(os, 'replace', side_effect=replace):
            self.save(SimpleNamespace(to_dict=lambda: {'round': 11}))
        self.assertEqual(json.loads(self.target.read_text()), {'round': 11})
        self.assertEqual(len(set(calls)), 1)
        self.assertNotEqual(calls[0], str(self.target) + '.tmp')
        self.assertEqual(self.logs, [])
        self.assertEqual(list(self.target.parent.iterdir()), [self.target])

    def test_serialization_failure_preserves_state(self):
        self.save(SimpleNamespace(to_dict=lambda: {'bad': object()}))
        self.assertEqual(json.loads(self.target.read_text()), {'round': 10})
        self.assertEqual(list(self.target.parent.iterdir()), [self.target])
        self.assertEqual(len(self.logs), 1)


if __name__ == '__main__':
    unittest.main()
