"""Actual binding and replay branches; hardware input is replaced by a receipt."""
import ast
import json
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def binding_context():
    tree = ast.parse((ROOT / 'autobtd6/helper.py').read_text())
    constants = {'_UNITY_SCANCODES', '_UNITY_NAMED', '_UNITY_MODIFIERS', '_SAVE_TOWER_NAMES'}
    selected = [node for node in tree.body if
                isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                    and target.id in constants for target in node.targets)
                or isinstance(node, ast.FunctionDef)
                    and node.name in ('unityBindingToKey', 'applyGameHotkeys')]
    context = dict(json=json, keybinds={'monkeys': {}, 'path': {},
                                      'others': {'play': 'Space'}, 'abilities': {}})
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<actual-bindings>', 'exec'), context)
    return context


class UnboundPlayTests(unittest.TestCase):
    def test_saved_unbound_play_clears_both_control_aliases(self):
        for binding in ({'path': ''}, {'path': '<Mouse>/leftButton'},
                        {'path': '<Keyboard>/space', 'modifierKey': 99}, None):
            with self.subTest(binding=binding):
                context = binding_context()
                gameplay = {'Sell': {'path': '<Keyboard>/backspace'}}
                if binding is not None:
                    gameplay['PlayFastForward'] = binding
                self.assertTrue(context['applyGameHotkeys'](json.dumps({'gameplay': gameplay})))
                self.assertIsNone(context['keybinds']['others']['round_start'])
                self.assertIsNone(context['keybinds']['others']['play'],
                                  'Automatic recovery must not retain a guessed Space binding')

    def test_rebound_play_and_absent_section_preserve_known_behavior(self):
        context = binding_context()
        context['applyGameHotkeys'](json.dumps({'gameplay': {
            'PlayFastForward': {'path': '<Keyboard>/p', 'modifierKey': 3}}}))
        self.assertEqual(context['keybinds']['others']['play'], '^{sc19}')
        self.assertEqual(context['keybinds']['others']['round_start'], '^{sc19}')
        context['applyGameHotkeys'](json.dumps({'gameplay': {}}))
        self.assertEqual(context['keybinds']['others']['play'], '^{sc19}',
                         'An absent section must not invent an unbound state')

    def test_automatic_round_gate_never_sends_an_unbound_key(self):
        source = (ROOT / 'autobtd6/replay.py').read_text()
        start = source.index('                    wantsToggle =')
        end = source.index('                # Repeating keys', start)
        code = textwrap.dedent(source[start:end])
        for key in (None, '^{sc19}'):
            with self.subTest(key=key):
                sent, logs = [], []
                context = dict(gameState='game_paused', fast=True, bestMatchDiff=0.001,
                    time=SimpleNamespace(time=lambda: 10.0), lastPlayToggleAt=0,
                    keybinds={'others': {'play': key}}, sendKey=sent.append,
                    customPrint=logs.append, playToggleIssued=False)
                exec(code, context)
                self.assertEqual(sent, [] if key is None else [key])
                self.assertEqual(context['playToggleIssued'], key is not None)
                if key is None:
                    self.assertTrue(any('unbound' in line for line in logs))
                    # The next frame must not spam another missing-binding warning.
                    logs.clear()
                    context['time'] = SimpleNamespace(time=lambda: 10.1)
                    exec(code, context)
                    self.assertFalse(logs)


if __name__ == '__main__':
    unittest.main()
