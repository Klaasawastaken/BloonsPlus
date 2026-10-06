"""Offline actual reader statements: no GUI, account or model loading."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ocr_tree = ast.parse((ROOT / 'autobtd6/ocr.py').read_text(encoding='utf-8'))
reader = next(node for node in ocr_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'parse_round_digits')
namespace = {}
exec(compile(ast.Module(body=[reader], type_ignores=[]), '<round-parser>', 'exec'), namespace)
parse = namespace['parse_round_digits']
replay = ast.parse((ROOT / 'autobtd6/replay.py').read_text(encoding='utf-8'))


class RoundCounterStructure(unittest.TestCase):
    def test_canonical_full_and_bare_counters(self):
        for limit in (40, 60, 80, 100):
            for round_number in (1, limit - 1, limit):
                self.assertEqual(parse(f'{round_number}/{limit}', limit), round_number)
                self.assertEqual(parse(str(round_number), limit), round_number)

    def test_phantom_digits_wrong_total_and_malformed_counters_are_rejected(self):
        for raw in ('82/80', '779/80', '79/100', '79/8', '079/80', '79/080',
                    '79/', '/80', '79/80/80', '0/80', '-1', ' 79', '７９/８０', None, '', '81'):
            self.assertEqual(parse(raw, 80), -1, raw)

    def test_actual_primary_and_fallback_statements_share_validation(self):
        primary = next(node for node in ast.walk(replay) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name)
                               and target.value.id == 'currentValues' for target in node.targets)
                       and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                       and node.value.func.id == 'parse_round_digits')
        fallback = next(node for node in ast.walk(replay) if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == 'alternateRound' for target in node.targets))
        for raw in ('82/80', '79/100', '779/80', '79/80', '79'):
            env = dict(parse_round_digits=parse, rawRound=raw, expectedRoundLimit=80,
                       currentValues={}, custom_ocr=lambda *args, **kwargs: raw, images=[None] * 4)
            exec(compile(ast.Module(body=[primary, fallback], type_ignores=[]), '<actual-readers>', 'exec'), env)
            self.assertEqual(env['currentValues']['round'], parse(raw, 80))
            self.assertEqual(env['alternateRound'], parse(raw, 80))

    def test_mode_limit_uses_target_mode_even_for_harder_source_recording(self):
        assignments = [next(node for node in ast.walk(replay) if isinstance(node, ast.Assign)
                            and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))
                       for name in ('modeValue', 'expectedRoundLimit')]
        modes = json.loads((ROOT / 'autobtd6/gamemodes.json').read_text())
        expected = dict(easy=40, primary_only=40, deflation=60, medium=60, military_only=60,
                        reverse=60, apopalypse=60, hard=80, magic_monkeys_only=80,
                        double_hp_moabs=80, half_cash=80, alternate_bloons_rounds=80,
                        impoppable=100, chimps=100)
        self.assertEqual(set(modes), set(expected))
        for mode, limit in expected.items():
            env = dict(gamemodes=modes, mapConfig={'gamemode': mode, 'sourceMode': 'chimps'})
            exec(compile(ast.Module(body=assignments, type_ignores=[]), '<mode-limit>', 'exec'), env)
            self.assertEqual(env['expectedRoundLimit'], limit, mode)


if __name__ == '__main__':
    unittest.main()
