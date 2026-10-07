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
                   _lastHeroPickerObservation=None, _heroPickerScanObservations=[])
        names = {'heroSelectionState', 'saveFailureShots', 'saveHeroPickerFailure', 'retainHeroPickerScanObservation'}
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

    def test_search_failure_keeps_earlier_title_pixels_and_excludes_account_area(self):
        with tempfile.TemporaryDirectory(prefix='bloons-hero-') as folder:
            env, _, logs = self.environment(folder)
            frame = np.full((1080, 1920, 3), 123, dtype=np.uint8)
            env['_lastHeroPickerObservation'] = dict(frame=frame, observedAt=1,
                monotonic=time.monotonic(), state={'title':'a', 'titleCandidates':['a','xps']})
            self.assertIn('retainHeroPickerScanObservation', env)
            env['retainHeroPickerScanObservation'](1, (140, 700))
            frame[:] = 0
            env['_lastHeroPickerObservation'] = dict(frame=frame, observedAt=2,
                monotonic=time.monotonic(), state={'title':'corvus'})
            env['pyautogui'] = SimpleNamespace()
            env['saveHeroPickerFailure']({'hero':'psi'}, 'hero-not-found', {})
            shots = list(Path(folder).glob('*_hero-picker-scan-00.png'))
            self.assertEqual(len(shots), 1)
            saved = cv2.imread(str(shots[0]))
            self.assertEqual(saved.shape, (1080,1920,3))
            self.assertTrue((saved[30:90,610:1300] == 123).all())
            self.assertTrue((saved[590:640,990:1240] == 123).all())
            self.assertFalse(saved[:100,1600:].any(), 'Account/currency area must not be retained')
            self.assertFalse(saved[800:].any())
            record=json.loads(next(line.split('HERO_PICKER_SCAN ',1)[1] for line in logs
                if line.startswith('HERO_PICKER_SCAN ')))
            self.assertEqual(record['page'],1)
            self.assertEqual(record['position'],[140,700])
            self.assertEqual(record['state']['titleCandidates'],['a','xps'])

    def test_scan_evidence_is_deduplicated_bounded_and_nonfatal(self):
        with tempfile.TemporaryDirectory(prefix='bloons-hero-') as folder:
            env, _, _ = self.environment(folder)
            self.assertIn('retainHeroPickerScanObservation', env)
            frame=np.zeros((108,192,3),dtype=np.uint8)
            for index in range(80):
                env['_lastHeroPickerObservation']=dict(frame=frame,observedAt=1,
                    monotonic=time.monotonic(),state={'title':str(index//2)})
                env['retainHeroPickerScanObservation'](0,(100,100))
            self.assertEqual(len(env['_heroPickerScanObservations']),40)
            for index in range(80,120):
                env['_lastHeroPickerObservation']['state']={'title':str(index)}
                env['retainHeroPickerScanObservation'](0,(100,100))
            self.assertEqual(len(env['_heroPickerScanObservations']),48)
            env['_heroPickerScanObservations']=[]
            env['_lastHeroPickerObservation']=None
            env['retainHeroPickerScanObservation'](0,(100,100))
            self.assertEqual(env['_heroPickerScanObservations'],[])

    def test_same_unreadable_text_keeps_different_title_pixels(self):
        with tempfile.TemporaryDirectory(prefix='bloons-hero-') as folder:
            env, _, _=self.environment(folder)
            frame=np.zeros((108,192,3),dtype=np.uint8)
            for index in (50,150):
                frame[2:10,60:120]=index
                env['_lastHeroPickerObservation']=dict(frame=frame,state={'title':'','button':'select'})
                env['retainHeroPickerScanObservation'](0,(index,100))
            self.assertEqual(len(env['_heroPickerScanObservations']),2)

    def test_scan_encode_failure_does_not_escape_or_retain_stale_data(self):
        with tempfile.TemporaryDirectory(prefix='bloons-hero-') as folder:
            env, frame, logs=self.environment(folder)
            env['_lastHeroPickerObservation']=dict(frame=frame,state={})
            def fail(*args):
                raise RuntimeError('synthetic encode failure')
            env['cv2']=SimpleNamespace(imencode=fail)
            env['retainHeroPickerScanObservation'](0,(100,100))
            self.assertEqual(env['_heroPickerScanObservations'],[])
            self.assertTrue(any('synthetic encode failure' in line for line in logs))

    def test_search_resets_scan_history_and_retains_each_actual_card(self):
        search=next(node for node in TREE.body if isinstance(node,ast.FunctionDef) and node.name=='findHeroCard')
        with tempfile.TemporaryDirectory(prefix='bloons-hero-') as folder:
            env, frame, _=self.environment(folder)
            env.update(LAST_HERO_FILE=Path(folder)/'missing.json', menuChangeDelay=0,
                sendKey=lambda _:None, heroAlreadySelected=lambda hero,state:state['title']==hero,
                imageAreas={'click':{'hero_positions':{'quincy':(100,100),'psi':(200,100)}}})
            titles=iter(['quincy','psi'])
            def observe():
                state={'title':next(titles),'button':'select'}
                env['_lastHeroPickerObservation']=dict(frame=frame,state=state)
                return state
            env.update(heroSelectionState=observe, _heroPickerScanObservations=[{'stale':True}],
                pyautogui=SimpleNamespace(size=lambda:(1920,1080),moveTo=lambda *a:None,
                    scroll=lambda *a:None,click=lambda *a:None))
            import sys
            sys.path.insert(0,str(ROOT/'autobtd6'))
            exec(compile(ast.Module(body=[search],type_ignores=[]),'<hero-search>','exec'),env)
            result=env['findHeroCard']('psi')
            self.assertEqual(result['title'],'psi')
            self.assertEqual([item['state']['title'] for item in env['_heroPickerScanObservations']],['quincy','psi'])

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
