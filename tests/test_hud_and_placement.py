"""Small offline regressions: no game imports, inputs, account files or TensorFlow."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
def functions(file, names, namespace):
    tree = ast.parse((ROOT / file).read_text(encoding='utf-8'))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(file), 'exec'), namespace)
    return namespace

class Regressions(unittest.TestCase):
    def test_clipped_screen_change_is_not_placement_evidence(self):
        tree = ast.parse((ROOT / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        function = next(node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef) and node.name == 'placementVisualCheck')
        env = {'np': np, 'cv2': cv2}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<placement-probe>', 'exec'), env)
        frame = np.full((1080,1920,3),255,dtype=np.uint8)
        for x,y,expected in ((13,600,False),(100,600,True),(1907,600,False),(100,13,False)):
            radius=max(30,int(1920*.021))
            crop=frame[max(0,y-radius):min(1080,y+radius),max(0,x-radius):min(1920,x+radius)]
            result,_=env['placementVisualCheck']({'pos':(x,y),'before':np.zeros_like(crop)},frame)
            self.assertEqual(result,expected,(x,y))

    def test_support_repositioning_requires_experiment_and_safe_mode(self):
        tree = ast.parse((ROOT / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        guard = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                     and any(isinstance(child, ast.Assign) and any(isinstance(t, ast.Name)
                             and t.id == 'nearbyReach' for t in child.targets) for child in node.body))
        for enabled, mode, dynamic, expected in (
                ('0', 'hard', False, False), ('1', 'chimps', False, False),
                ('1', 'hard', True, False), ('1', 'hard', False, True)):
            env = dict(os=SimpleNamespace(environ={'BLOONS_EXPERIMENTAL_PLACEMENT':enabled}),
                       mapConfig={'gamemode':mode}, dynamicHere=dynamic,
                       supportPx=100, allies=[(1,1)], originVerdict=False)
            result = eval(compile(ast.Expression(guard.test), '<support-guard>', 'eval'),env)
            self.assertEqual(bool(result),expected,(enabled,mode,dynamic))

    def test_cash_does_not_invent_digits(self):
        env = functions('autobtd6/ocr.py', ['parse_cash_digits', 'cash_ocr'], {})
        parse = env['parse_cash_digits']
        for raw in ('0000', '01', '5/60', '-1', '', None, '１２３'):
            self.assertEqual(parse(raw), -1)
        self.assertEqual(parse('0'), 0)
        self.assertEqual(parse('40000'), 40000)
        # This is suspicious, but must never silently become 40,000.
        self.assertEqual(parse('540006'), 540006)
        reads = {224: '0000', 230: '40000', 242: '40000'}
        env['custom_ocr'] = lambda img, resolution, white_threshold=224: reads[white_threshold]
        self.assertEqual(env['cash_ocr'](None, (2560, 1440)), 40000)
        reads[242] = '40008'
        self.assertEqual(env['cash_ocr'](None, (2560, 1440)), -1)
        reads[224] = '0'
        self.assertEqual(env['cash_ocr'](None, (2560, 1440)), 0)

    def test_round_recovery_requires_complete_counter(self):
        read = functions('autobtd6/ocr.py', ['round_recovery_candidate'], {})['round_recovery_candidate']
        self.assertTrue(read('19/60', 10, 30))
        self.assertFalse(read('19', 10, 30))
        self.assertFalse(read('619/60', 10, 100))
        self.assertFalse(read('9/60', 10, 30))
        self.assertFalse(read('19/60', 10, 1))
        self.assertFalse(read('779/80', 79, 30))

    def test_offset_cash_glyph(self):
        class Model:
            def predict(self, glyphs, **kwargs):
                rows = np.zeros((len(glyphs), 11)); rows[:, 7] = 1
                return rows
        env = functions('autobtd6/ocr.py', ['custom_ocr'], {
            'np': np, 'cv2': cv2, 'pyautogui': SimpleNamespace(size=lambda: (1920,1080)),
            '_get_ocr_model': lambda: Model(),
        })
        crop = np.zeros((50,150,3), dtype=np.uint8)
        crop[10:40,80:96] = 255
        self.assertEqual(env['custom_ocr'](crop), '7')

    def test_play_and_nudge_are_not_confirmation(self):
        env = functions('autobtd6/replay.py', ['confirmButtonVisible'], {
            'np': np, 'CONFIRM_BUTTON_1080': (1600,205), '_confirmButton1080': (1600,205),
        })
        frame = np.zeros((1080,1920,3), dtype=np.uint8)
        frame[990:1080,1770:1860] = (0,255,0)
        frame[990:1080,1645:1745] = (0,0,255)
        self.assertFalse(env['confirmButtonVisible'](frame))
        # Green terrain beside a red cancel button also isn't a check mark.
        frame[12:76,1570:1630] = (0,255,0)
        frame[85:153,1567:1632] = (0,0,255)
        self.assertFalse(env['confirmButtonVisible'](frame))
        frame[25:55,1585:1610] = 255
        self.assertTrue(env['confirmButtonVisible'](frame))
        self.assertEqual(env['_confirmButton1080'], (1600,44))

if __name__ == '__main__': unittest.main()
