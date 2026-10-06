import ast
import importlib.util
import textwrap
import unittest
import tempfile
import io
from contextlib import redirect_stdout
from unittest.mock import patch
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

    def test_actual_source_assignment_and_remaining_manual_exclusions(self):
        route = converter.convert_btd6bot(ROOT / 'btd6bot/btd6bot/plans/infernalMediumApopalypse.py')
        self.assertEqual(route.source_loop_trace, [(1, 1)])
        self.assertFalse(any('reassignment' in item for item in route.harmless))
        route = converter.convert_btd6bot(ROOT / 'btd6bot/btd6bot/plans/sanctuaryHardChimps.py')
        self.assertEqual(route.source_loop_trace[:3], [(6, 6), (7, 7), (8, 8)])
        self.assertNotIn('forward() control omitted', route.lossy)
        self.assertNotIn('end_round() control omitted', route.lossy)
        self.assertEqual(route.source_round_trace[0], (6, 'initial'))
        self.assertEqual(route.source_round_trace[1], (7, 'after-play'))
        self.assertFalse(route.lossy)
        self.assertTrue(any(state.get('spikeTarget') == 'automatic' for state in route.towers.values()))

    def test_manual_skip_is_consumed_by_empty_iteration(self):
        route = self.convert('''
            if round == BEGIN:
                forward(1)
                end_round(2)
            elif round == 3:
                wait(3)
        ''', end=3)
        self.assertEqual(route.lines, [
            'autostart on', 'source round 1', 'play once', 'wait 0.2 seconds',
            'wait 2 seconds', 'play once', 'wait 0.2 seconds',
            'source round 2 after play', 'round 3', 'source round 3', 'wait 3 seconds'])
        self.assertEqual(route.source_round_trace, [(1, 'initial'), (2, 'after-play'), (3, 'hud')])
        self.assertFalse(route.lossy)

    def test_end_round_does_not_suppress_implicit_forward(self):
        route = self.convert('''
            if round == BEGIN:
                change_autostart()
                end_round()
            elif round == 3:
                wait(3)
        ''', end=3)
        self.assertEqual(route.lines, [
            'autostart on', 'source round 1', 'autostart off',
            'play once', 'wait 0.2 seconds', 'play twice',
            'source round 2 after play', 'round 3', 'source round 3', 'wait 3 seconds'])

    def test_forward_after_reassignment_does_not_invent_hud_jump(self):
        route = self.convert('''
            if round == BEGIN:
                forward()
                round = 3
            if round == 3:
                end_round(time_limit=1.5)
            elif round == 4:
                wait(4)
        ''', end=4)
        self.assertEqual(route.source_loop_trace, [(1, 1), (1, 3), (4, 4)])
        self.assertEqual(route.source_round_trace, [(1, 'initial'), (4, 'after-play')])
        self.assertNotIn('round 3', route.lines)
        self.assertIn('wait 1.5 seconds', route.lines)

    def test_manual_commands_require_literal_supported_arguments(self):
        for command in ('forward(0)', 'forward(3)', 'forward(True)', 'forward(1.0)',
                        'forward(unknown)', 'forward(1, speed=1)', 'forward(extra=1)',
                        'end_round(-1)', 'end_round(True)', 'end_round(1, 2)',
                        'end_round(unknown)', 'end_round(timer=1)'):
            with self.subTest(command=command), self.assertRaises(converter.Unsupported):
                self.convert('if round == BEGIN:\n    '+command+'\n', end=2)
        route = self.convert('if round == BEGIN:\n    forward(speed=2)\n    end_round(time_limit=0)\n', end=2)
        self.assertEqual(route.lines.count('play twice'), 1)
        self.assertEqual(route.lines.count('play once'), 1)

    def test_deflation_forward_two_is_not_replaced_with_absolute_fast(self):
        route = converter.convert_btd6bot(ROOT / 'btd6bot/btd6bot/plans/dark_castleEasyDeflation.py')
        self.assertEqual(route.source_round_trace[0], (31, 'initial'))
        self.assertEqual(route.lines.count('play twice'), 1)
        self.assertNotIn('start round fast', route.lines)
        self.assertFalse(route.lossy)

    def test_autostart_only_plan_still_starts_after_first_body(self):
        route = self.convert('''
            if round == BEGIN:
                change_autostart()
                wait(1)
            elif round == 2:
                change_autostart()
        ''', end=2)
        self.assertEqual(route.lines, ['autostart on', 'source round 1', 'autostart off',
            'wait 1 seconds', 'play twice', 'round 2', 'source round 2', 'autostart on'])

    def test_candidate_batch_is_separate_idempotent_and_preserves_user_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            original = output / 'logs#chimps#1920x1080.btd6'
            original.write_bytes(b'original CHIMPS recording\n')
            with patch.object(converter, 'PT', output), patch.object(converter, 'validate', return_value={}), redirect_stdout(io.StringIO()):
                converter.emit_manual_candidates()
                before = {p.name: p.read_bytes() for p in output.glob('*.btd6')}
                self.assertEqual(len(before), 13)
                for name in ('last_resort', 'erosion', 'sanctuary', 'sunset_gulch'):
                    self.assertTrue(any(file.startswith(name+'#') for file in before),name)
                converter.emit_manual_candidates()
                self.assertEqual(before, {p.name: p.read_bytes() for p in output.glob('*.btd6')})
                self.assertEqual(original.read_bytes(), b'original CHIMPS recording\n')
                edited = next(output.glob('*#manual-preserved.btd6'))
                edited.write_bytes(b'user route edit\n')
                with self.assertRaisesRegex(RuntimeError, 'Refusing to overwrite'):
                    converter.emit_manual_candidates()
                self.assertEqual(edited.read_bytes(), b'user route edit\n')

    def test_validator_counts_new_control_commands_using_actual_parser_actions(self):
        # Exercise the subprocess validator itself with an inert helper, so the
        # line-count gate cannot silently drop a new command or a trailing typo.
        import sys
        from types import SimpleNamespace
        commands = ['autostart on', 'source round 6', 'play twice', 'wait 0.2 seconds',
                    'play once', 'source round 7 after play']
        actions = ['set_autostart', 'source_round', 'play_twice', 'await_delay', 'play_once', 'source_round']
        name = 'logs#chimps#1920x1080#manual-preserved.btd6'
        helper = SimpleNamespace(parseBTD6InstructionsFile=lambda *args, **kwargs: {
            'map': 'logs', 'monkeys': {}, 'steps': [{'action': action} for action in actions]},
            towers={}, maps={'logs': {}})
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / name
            target.write_text('\n'.join(commands), encoding='utf-8')
            from unittest.mock import mock_open
            fake_open = mock_open(read_data=target.read_text(encoding='utf-8'))
            with patch.dict(sys.modules, {'helper': helper}), patch('sys.stdin', io.StringIO('["'+name+'"]')), patch('builtins.open', fake_open), redirect_stdout(io.StringIO()) as result:
                exec(converter.VALIDATOR, {})
            self.assertIn('"'+name+'": ""', result.getvalue())
            helper.parseBTD6InstructionsFile = lambda *args, **kwargs: {'map': 'logs', 'monkeys': {}, 'steps': []}
            with patch.dict(sys.modules, {'helper': helper}), patch('sys.stdin', io.StringIO('["'+name+'"]')), patch('builtins.open', fake_open), redirect_stdout(io.StringIO()) as result:
                exec(converter.VALIDATOR, {})
            self.assertIn('6 recognised, 0 parsed', result.getvalue())


if __name__ == '__main__': unittest.main()
