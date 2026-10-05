import ast
from pathlib import Path
import unittest


class HudTransition(unittest.TestCase):
    def test_right_to_left_panel_resets_round_crop(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        nodes = None
        for parent in ast.walk(tree):
            body = getattr(parent, 'body', None)
            if not isinstance(body, list):
                continue
            for i, node in enumerate(body):
                if isinstance(node, ast.FunctionDef) and node.name == 'gameBox':
                    end = next(j for j in range(i+1, len(body)) if isinstance(body[j], ast.Assign)
                               and any(isinstance(t, ast.Name) and t.id == 'images' for t in body[j].targets))
                    nodes = body[i:end]
        self.assertIsNotNone(nodes)
        normal = {'lives': [1,2,3,4], 'money': [5,6,7,8], 'round': [1434,29,1560,71]}
        env = dict(scale=2, mapConfig={}, segmentCoordinates=dict(normal),
                   getIngameOcrSegments=lambda _: dict(normal))
        code = compile(ast.Module(body=nodes, type_ignores=[]), '<hud-layout>', 'exec')
        for left, right in [(False, True), (True, False), (False, False)]:
            env.update(hudPanelOpen=left, hudRightPanelOpen=right)
            exec(code, env)
            expected = [1010,34,1224,78] if right else normal['round']
            self.assertEqual(env['segmentCoordinates']['round'], expected, (left, right))
