"""Client rectangle diagnostics without touching windows or sending input."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

class WindowGeometry(unittest.TestCase):
    def run_client(self, width, height):
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root / 'autobtd6/windowed_input.py').read_text(encoding='utf-8'))
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'game_client')
        env = dict(_cached_hwnd=1, _find_game_window=lambda: 1,
                   _Rect=lambda: SimpleNamespace(left=0, top=0, right=width, bottom=height),
                   _Point=lambda *_: SimpleNamespace(x=10, y=20),
                   ctypes=SimpleNamespace(byref=lambda value: value),
                   _user32=SimpleNamespace(IsIconic=lambda _: False, GetClientRect=lambda *_: True, ClientToScreen=lambda *_: True),
                   time=SimpleNamespace(sleep=lambda _: None))
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<actual-game-client>', 'exec'), env)
        return env['game_client']()

    def test_non_game_rectangle_preserves_transition_reason(self):
        with self.assertRaisesRegex(RuntimeError, 'transitioning.*304x201'):
            self.run_client(304, 201)

    def test_small_game_rectangle_preserves_not_ready_reason(self):
        with self.assertRaisesRegex(RuntimeError, 'not ready yet.*320x180'):
            self.run_client(320, 180)

    def test_zero_area_remains_minimized(self):
        with self.assertRaisesRegex(RuntimeError, 'minimized'):
            self.run_client(0, 0)

    def test_ready_rectangle_is_returned(self):
        self.assertEqual(self.run_client(1920, 1080), (10, 20, 1920, 1080))

if __name__ == '__main__':
    unittest.main()
