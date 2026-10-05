"""Moving covers/lanes must not relocate stationary tower click points."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class TowerTrackingScope(unittest.TestCase):
    def test_only_moving_platforms_relocate_towers(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        helper = next((node for node in tree.body if isinstance(node, ast.FunctionDef)
                       and node.name == 'hasMovingTowerPlatforms'), None)
        self.assertIsNotNone(helper, 'Coordinate tracking needs its own platform gate')
        env = {'os': os}
        exec(compile(ast.Module(body=[helper], type_ignores=[]), '<platform-gate>', 'exec'), env)
        gate = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                    and any(isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                            and call.func.attr == 'locate' for call in ast.walk(node))
                    and 'hasMovingTowerPlatforms' in ast.unparse(node.test))
        calls = []
        env.update(towerTracker=SimpleNamespace(locate=lambda *a: calls.append(a) or None),
                   towerName='heli1', screenshot=object())
        with patch.dict(os.environ, {'BLOONS_DYNAMIC_PLACEMENT':'1', 'BLOONS_MOVING_PLATFORMS':'0'}):
            for name in ('polyphemus', 'one_two_tree', 'x_factor', 'muddy_puddles', 'tricky_tracks',
                         'covered_garden', 'glacial_trail', 'erosion', 'bloonarius_prime'):
                env['mapConfig'] = {'map':name}
                exec(compile(ast.Module(body=[gate], type_ignores=[]), '<tracking>', 'exec'), env)
            self.assertEqual(calls, [], 'Dynamic access alone cannot move click coordinates')
            for name in ('geared', 'sanctuary'):
                self.assertTrue(env['hasMovingTowerPlatforms'](name))
                env['mapConfig'] = {'map':name}
                exec(compile(ast.Module(body=[gate], type_ignores=[]), '<tracking>', 'exec'), env)
            self.assertEqual(len(calls), 2, 'Actual moving platforms must still run tracking')
        with patch.dict(os.environ, {'BLOONS_MOVING_PLATFORMS':'1'}):
            self.assertTrue(env['hasMovingTowerPlatforms']('future_platform_map'))
            env['mapConfig'] = {'map':'future_platform_map'}
            exec(compile(ast.Module(body=[gate], type_ignores=[]), '<tracking>', 'exec'), env)
            self.assertEqual(len(calls), 3)


if __name__ == '__main__':
    unittest.main()
