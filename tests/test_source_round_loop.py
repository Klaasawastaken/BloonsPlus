import ast
import importlib.util
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('round_loop_import', ROOT / 'tools/import-public-routes.py')
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class SourceRoundLoopTests(unittest.TestCase):
    def convert(self, branches, begin=1, end=10):
        source = 'while round < END + 1:\n    round = Rounds.round_check(round, map_start, data[2])\n'
        source += textwrap.indent(textwrap.dedent(branches), '    ')
        route = converter.Route('btd6bot', 'fixture', 'logs', 'easy')
        converter.convert_btd6bot_loop(route, ast.parse(source).body[0], begin, end)
        return route

    def test_branch_order_is_chronological_not_textual(self):
        route = self.convert('''
            if round == BEGIN:
                wait(1)
            elif round == 9:
                wait(9)
            elif round == 7:
                wait(7)
        ''')
        self.assertEqual(route.lines, ['wait 1 seconds', 'round 7', 'wait 7 seconds', 'round 9', 'wait 9 seconds'])
        self.assertEqual(route.source_loop_trace, [(1, 1), (7, 7), (9, 9)])

    def test_independent_chains_both_execute_same_iteration_elif_only_once(self):
        route = self.convert('''
            if round == BEGIN:
                wait(1)
            elif round == BEGIN:
                wait(99)
            if round == BEGIN:
                wait(2)
            elif round == 3:
                wait(3)
        ''')
        self.assertEqual(route.lines, ['wait 1 seconds', 'wait 2 seconds', 'round 3', 'wait 3 seconds'])
        self.assertEqual(route.source_loop_trace, [(1, 1), (1, 1), (3, 3)])

    def test_reassignment_affects_later_root_and_skips_future_iterations(self):
        route = self.convert('''
            if round == BEGIN:
                wait(1)
                round = END
                wait(2)
            elif round == 2:
                wait(99)
            if round == END:
                wait(3)
        ''')
        self.assertEqual(route.lines, ['wait 1 seconds', 'wait 2 seconds', 'wait 3 seconds'])
        self.assertEqual(route.source_loop_trace, [(1, 1), (1, 10)])
        self.assertFalse(route.harmless)

    def test_forward_jump_uses_round_check_entry_not_reassigned_hud_value(self):
        route = self.convert('''
            if round == BEGIN:
                round = 7
            if round == 7:
                wait(7)
            elif round == 8:
                wait(8)
        ''')
        self.assertEqual(route.lines, ['wait 7 seconds', 'round 8', 'wait 8 seconds'])
        self.assertEqual(route.source_loop_trace, [(1, 1), (1, 7), (8, 8)])

    def test_nonstandard_or_backward_control_is_rejected(self):
        for body in ('if round == BEGIN:\n    round = 0\n',
                     'if round == 4:\n    round = 3\n',
                     'if round == BEGIN:\n    round = False\n',
                     'if round == BEGIN:\n    round = unknown\n',
                     'if round == BEGIN:\n    round = 11\n',
                     'if round > 3:\n    wait(2)\n',
                     'wait(2)\nif round == BEGIN:\n    pass\n',
                     'if round == BEGIN:\n    pass\nelse:\n    wait(2)\n'):
            with self.subTest(body=body), self.assertRaises(converter.Unsupported): self.convert(body)
        with self.assertRaises(converter.Unsupported):
            converter.btd6bot_statement(converter.Route('btd6bot', 'fixture', 'logs', 'easy'),
                                       ast.parse('round = END').body[0])

    def test_loop_header_cannot_hide_extra_input(self):
        for source in ('while True:\n    pass',
                       'while round < END + 1:\n    round = evil()\n    if round == BEGIN:\n        pass',
                       'while round < END + 1:\n    round = Rounds.round_check(round, map_start, unknown)\n    if round == BEGIN:\n        pass'):
            with self.assertRaises(converter.Unsupported):
                converter.convert_btd6bot_loop(converter.Route('btd6bot', 'fixture', 'logs', 'easy'),
                                               ast.parse(source).body[0], 1, 10)

    def test_actual_source_assignment_and_manual_exclusions(self):
        route = converter.convert_btd6bot(ROOT / 'btd6bot/btd6bot/plans/infernalMediumApopalypse.py')
        self.assertEqual(route.source_loop_trace, [(1, 1)])
        self.assertFalse(any('reassignment' in item for item in route.harmless))
        route = converter.convert_btd6bot(ROOT / 'btd6bot/btd6bot/plans/sanctuaryHardChimps.py')
        self.assertEqual(route.source_loop_trace[:3], [(6, 6), (7, 7), (8, 8)])
        self.assertIn('forward() control omitted', route.lossy)
        self.assertIn('end_round() control omitted', route.lossy)


if __name__ == '__main__': unittest.main()
