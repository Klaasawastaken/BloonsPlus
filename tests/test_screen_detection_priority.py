"""Menu-color fallback must not override positively recognized game screens."""
import ast
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load_detector():
    helper = ast.parse((ROOT / 'autobtd6/helper.py').read_text(encoding='utf-8'))
    replay = ast.parse((ROOT / 'autobtd6/replay.py').read_text(encoding='utf-8'))
    nodes = [next(n for n in helper.body if isinstance(n, ast.ClassDef) and n.name == 'Screen')]
    nodes += [n for n in replay.body if isinstance(n, ast.FunctionDef)
              and n.name in ('mapSelectionChromeVisible', 'recognizeScreen')]
    env = {'Enum': Enum, 'windowed_input': SimpleNamespace(is_game_foreground=lambda: True)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<production screen functions>', 'exec'), env)
    return env


def menu_colored_frame(width=1920):
    height = width * 9 // 16
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for box, color in [((25, 20, 125, 115), (200, 150, 20)),
                       ((1600, 385, 1720, 490), (20, 150, 200)),
                       ((1260, 885, 1420, 1050), (20, 150, 200))]:
        x1, y1, x2, y2 = [round(v * width / 1920) for v in box]
        frame[y1:y2, x1:x2] = color
    return frame


class ScreenDetectionPriorityTests(unittest.TestCase):
    def test_known_screen_wins_over_incidental_menu_colors(self):
        env = load_detector()
        for width in (1920, 2560):
            frame = menu_colored_frame(width)
            self.assertTrue(env['mapSelectionChromeVisible'](frame))
            for screen in env['Screen']:
                if screen in (env['Screen'].UNKNOWN, env['Screen'].BTD6_UNFOCUSED):
                    continue
                with self.subTest(width=width, screen=screen.name):
                    env['_recognizeScreen'] = lambda *args, result=screen, **kwargs: result
                    self.assertEqual(env['recognizeScreen'](frame, {}), screen)

    def test_unknown_map_page_still_uses_color_fallback(self):
        env = load_detector()
        env['_recognizeScreen'] = lambda *args, **kwargs: env['Screen'].UNKNOWN
        self.assertEqual(env['recognizeScreen'](menu_colored_frame(), {}), env['Screen'].MAP_SELECTION)
        self.assertEqual(env['recognizeScreen'](np.zeros((1080, 1920, 3), np.uint8), {}), env['Screen'].UNKNOWN)

    def test_focus_gate_and_home_button_priority_stay_intact(self):
        env = load_detector()
        env['windowed_input'].is_game_foreground = lambda: False
        env['_recognizeScreen'] = lambda *args, **kwargs: env['Screen'].MAP_SELECTION
        frame = menu_colored_frame()
        self.assertEqual(env['recognizeScreen'](frame, {}), env['Screen'].BTD6_UNFOCUSED)
        self.assertEqual(env['recognizeScreen'](frame, {}, ignoreFocus=True), env['Screen'].MAP_SELECTION)
        for y in (1210, 1320):
            frame[round(y * .75), 960] = (0, 255, 0)
        self.assertEqual(env['recognizeScreen'](frame, {}, ignoreFocus=True), env['Screen'].STARTMENU)


if __name__ == '__main__':
    unittest.main()
