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
    def test_round_recovery_requires_complete_counter(self):
        read = functions('autobtd6/ocr.py', ['round_recovery_candidate'], {})['round_recovery_candidate']
        self.assertTrue(read('19/60', 10, 30))
        self.assertFalse(read('19', 10, 30))
        self.assertFalse(read('619/60', 10, 100))
        self.assertFalse(read('9/60', 10, 30))
        self.assertFalse(read('19/60', 10, 1))

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
