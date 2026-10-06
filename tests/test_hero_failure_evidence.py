"""Pre-game hero errors must preserve the frame actually passed to OCR."""
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from types import SimpleNamespace

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TREE = ast.parse((ROOT / 'autobtd6/replay.py').read_text(encoding='utf-8'))


class HeroFailureEvidence(unittest.TestCase):
    def environment(self, folder, output=b'{"title":"obyilgrecnfoot","button":"select","greenFraction":0.489}'):
        frame = np.zeros((12, 16, 3), dtype=np.uint8)
        frame[:, :, 0] = 180
        logs = []
        env = dict(np=np, cv2=cv2, os=os, time=time, json=json,
                   pyautogui=SimpleNamespace(screenshot=lambda: frame.copy()),
                   subprocess=SimpleNamespace(run=lambda *a, **k: SimpleNamespace(returncode=0, stdout=output)),
                   customPrint=logs.append, FAILURE_SHOT_DIR=folder, FAILURE_SHOTS_KEPT=60,
                   _lastHeroPickerObservation=None)
        names = {'heroSelectionState', 'saveFailureShots', 'saveHeroPickerFailure'}
        functions = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in names]
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<hero-evidence>', 'exec'), env)
        return env, frame, logs

    def test_failure_saves_exact_ocr_frame_without_another_capture_or_input(self):
        with tempfile.TemporaryDirectory(prefix='bloons-hero-') as folder:
            env, frame, logs = self.environment(folder)
            with contextlib.redirect_stdout(io.StringIO()):
                state = env['heroSelectionState']()
            # A later desktop capture or gameplay input would be the wrong evidence.
            env['pyautogui'] = SimpleNamespace()
            self.assertTrue('saveHeroPickerFailure' in env, 'Hero failures currently have no screenshot/evidence path')
            env['saveHeroPickerFailure']({'map':'dark_castle', 'gamemode':'impoppable', 'hero':'obyn_greenfoot'},
                                        'select-unconfirmed', state, attempts=3, position=(1110, 619))
            shots = list(Path(folder).glob('*_hero-picker.png'))
            self.assertEqual(len(shots), 1)
            np.testing.assert_array_equal(cv2.imread(str(shots[0])), frame[:, :, ::-1])
            self.assertTrue(any(line == 'FAILURE_SHOT ' + str(shots[0].resolve()) for line in logs))
            record = json.loads(next(line.split('ERROR HERO_PICKER_FAILURE ', 1)[1]
                                     for line in logs if line.startswith('ERROR HERO_PICKER_FAILURE ')))
            self.assertEqual(record['hero'], 'obyn_greenfoot')
            self.assertEqual(record['state']['title'], 'obyilgrecnfoot')
            self.assertEqual(record['attempts'], 3)
            self.assertEqual(record['position'], [1110, 619])
            self.assertEqual(record['frameSize'], [16, 12])
            self.assertEqual(record['freshness'], 'fresh')
            self.assertGreaterEqual(record['ageSeconds'], 0)

    def test_malformed_ocr_state_does_not_replace_evidence_with_unrelated_data(self):
        with tempfile.TemporaryDirectory(prefix='bloons-hero-') as folder:
            env, frame, logs = self.environment(folder, b'[]')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(env['heroSelectionState'](), {})
            self.assertIsInstance(env['_lastHeroPickerObservation'], dict)
            self.assertEqual(env['_lastHeroPickerObservation']['state'], {})
            np.testing.assert_array_equal(env['_lastHeroPickerObservation']['frame'], frame[:, :, ::-1])

    def test_stale_frame_is_explicit_and_missing_frame_is_not_invented(self):
        with tempfile.TemporaryDirectory(prefix='bloons-hero-') as folder:
            env, _, logs = self.environment(folder)
            with contextlib.redirect_stdout(io.StringIO()):
                state = env['heroSelectionState']()
            env['_lastHeroPickerObservation']['monotonic'] -= 60
            env['saveHeroPickerFailure']({'hero':'psi'}, 'button-unconfirmed', state)
            record = json.loads(logs[0].split('ERROR HERO_PICKER_FAILURE ', 1)[1])
            self.assertEqual(record['freshness'], 'stale')
            self.assertGreaterEqual(record['ageSeconds'], 60)
            env['_lastHeroPickerObservation'] = None
            logs.clear()
            env['saveHeroPickerFailure']({'hero':'psi'}, 'button-unconfirmed', {})
            record = json.loads(logs[0].split('ERROR HERO_PICKER_FAILURE ', 1)[1])
            self.assertEqual(record['freshness'], 'missing')
            self.assertIsNone(record['observedAt'])
            self.assertIsNone(record['frameSize'])
            self.assertFalse(any(line.startswith('FAILURE_SHOT ') for line in logs))

    def test_all_terminal_picker_branches_save_evidence_before_exit(self):
        main = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        branch = next(node for node in ast.walk(main) if isinstance(node, ast.If)
                      and isinstance(node.test, ast.Compare) and any(
                          isinstance(value, ast.Attribute) and value.attr == 'SELECT_HERO'
                          for value in node.test.comparators))
        match = next(node for node in TREE.body if isinstance(node, ast.FunctionDef)
                     and node.name == 'heroAlreadySelected')
        for state, reason in [({'title':'sauda', 'button':'selected'}, 'hero-not-found'),
                              ({'title':'obyngreenfoot', 'button':'select'}, 'select-unconfirmed'),
                              ({'title':'obyngreenfoot', 'button':'unknown'}, 'button-unconfirmed')]:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory(prefix='bloons-hero-') as folder:
                env, _, logs = self.environment(folder, json.dumps(state).encode())
                env.update(screen='STARTMENU', Screen=SimpleNamespace(STARTMENU='STARTMENU'),
                           mapConfig={'map':'dark_castle', 'gamemode':'impoppable', 'hero':'obyn_greenfoot',
                                      'steps':[{'action':'place', 'type':'hero'}]},
                           resolveRouteHero=lambda _: 'obyn_greenfoot', readLastHero=lambda: 'sauda',
                           towers={'heros':{'obyn_greenfoot':{'class':'land'}}}, menuChangeDelay=0,
                           imageAreas={'click':{'screen_startmenu_button_hero_selection':(1, 2),
                                               'hero_positions':{'obyn_greenfoot':(112, 420)},
                                               'screen_hero_selection_select_hero':(1110, 619)}},
                           findHeroCard=lambda _: {}, sys=SimpleNamespace(exit=lambda code: (_ for _ in ()).throw(SystemExit(code))))
                env['pyautogui'].click = lambda *a: None
                env['pyautogui'].moveTo = lambda *a, **k: None
                env['time'] = SimpleNamespace(sleep=lambda _:None, time=time.time, monotonic=time.monotonic, strftime=time.strftime)
                exec(compile(ast.Module(body=[match], type_ignores=[]), '<hero-match>', 'exec'), env)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as stopped:
                    exec(compile(ast.Module(body=branch.body, type_ignores=[]), '<hero-flow>', 'exec'), env)
                self.assertEqual(stopped.exception.code, 2)
                records = [json.loads(line.split('ERROR HERO_PICKER_FAILURE ', 1)[1]) for line in logs
                           if line.startswith('ERROR HERO_PICKER_FAILURE ')]
                self.assertEqual([record['reason'] for record in records], [reason])
                self.assertEqual(len(list(Path(folder).glob('*_hero-picker.png'))), 1)


if __name__ == '__main__':
    unittest.main()
