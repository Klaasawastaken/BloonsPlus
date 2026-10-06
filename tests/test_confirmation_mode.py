"""Placement confirmation is discovered live, without game input or filesystem writes."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]


def replay_tree():
    return ast.parse((ROOT / 'autobtd6/replay.py').read_text(encoding='utf-8'))


class ConfirmationMode(unittest.TestCase):
    def test_old_flag_cannot_enable_confirmation_for_new_replay(self):
        tree = replay_tree()
        assignment = next(node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == 'confirmPlacementMode'
                                  for target in node.targets))
        env = {'os': SimpleNamespace(path=SimpleNamespace(exists=lambda _: True, join=lambda *_: 'old.flag')),
               'KNOWN_SPOTS_DIR': 'private'}
        exec(compile(ast.Module(body=[assignment], type_ignores=[]), '<actual-mode-init>', 'exec'), env)
        self.assertIs(env['confirmPlacementMode'], False)

    def run_observed_check(self, visible):
        tree = replay_tree()
        branch = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                      and isinstance(node.test, ast.Call) and isinstance(node.test.func, ast.Name)
                      and node.test.func.id == 'confirmButtonVisible'
                      and len(node.test.args) == 1 and isinstance(node.test.args[0], ast.Name)
                      and node.test.args[0].id == 'afterClick')
        clicks, writes = [], []
        env = dict(confirmPlacementMode=False, afterClick=SimpleNamespace(shape=(1080, 1920, 3)),
                   confirmButtonVisible=lambda _: visible, confirmButtonPos=lambda _: (1600, 205),
                   pyautogui=SimpleNamespace(click=clicks.append), customPrint=lambda _: None,
                   action={'name': 'heli0', 'pos': (103, 600)}, KNOWN_SPOTS_DIR='private',
                   os=SimpleNamespace(makedirs=lambda *a, **kw: writes.append('mkdir'),
                                      path=SimpleNamespace(join=lambda *_: 'old.flag')),
                   open=lambda *a, **kw: (writes.append('flag') or SimpleNamespace(close=lambda: None)))
        exec(compile(ast.Module(body=[branch], type_ignores=[]), '<actual-confirm-check>', 'exec'), env)
        return env['confirmPlacementMode'], clicks, writes

    def test_visible_check_enables_mode_and_clicks_without_persistent_flag(self):
        mode, clicks, writes = self.run_observed_check(True)
        self.assertTrue(mode)
        self.assertEqual(clicks, [(1600, 205)])
        self.assertEqual(writes, [])

    def test_absent_check_sends_no_confirmation_click(self):
        mode, clicks, writes = self.run_observed_check(False)
        self.assertFalse(mode)
        self.assertEqual(clicks, [])
        self.assertEqual(writes, [])


if __name__ == '__main__':
    unittest.main()
