import ast
import io
import re
import sys
import textwrap
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'autobtd6'))
from source_round import drive_source_round, restore_source_round_context, source_round_anchor
from route_timing import ability_ready
from game_runtime import normalize_action
from purchase_pacing import pacing_allowed
from autostart_control import parse_autostart_command


class SourceRoundTests(unittest.TestCase):
    def marker(self, after=False):
        return dict(action='source_round', round=7, afterPlay=after, cost=0, routeStepIndex=2)

    def test_logical_clock_does_not_replace_observed_round(self):
        config = {'steps': [self.marker()], 'observedRound': 6}
        checkpoint = {'round': 6}
        self.assertTrue(drive_source_round(config, checkpoint, 20))
        self.assertEqual(config['sourceRoundContext'], {'round': 7, 'startedAt': 20, 'index': 2})
        self.assertEqual(config['observedRound'], 6)
        self.assertEqual(checkpoint['round'], 6)
        self.assertEqual(config['steps'], [])

    def test_after_play_uses_input_clock_not_late_observation(self):
        config = {'steps': [self.marker(True)], 'sourcePlay': {'index': 1, 'sentAt': 10}}
        drive_source_round(config, None, 14)
        self.assertEqual(config['sourceRoundContext']['startedAt'], 10.2)
        config['sourceRoundTiming'] = True
        step = dict(action='ability', timer=5, sourceTiming=True)
        self.assertFalse(ability_ready(step, 15, source_round_anchor(config, 14)))
        self.assertTrue(ability_ready(step, 15.2, source_round_anchor(config, 14)))

    def test_missing_future_negative_or_reused_play_evidence_retains_marker(self):
        for play, previous in ((None, None), ({'index': -1, 'sentAt': 10}, None),
                               ({'index': 3, 'sentAt': 10}, None),
                               ({'index': 1, 'sentAt': 10}, {'index': 1})):
            step = self.marker(True)
            config = {'steps': [step], 'sourcePlay': play, 'sourceRoundContext': previous}
            self.assertTrue(drive_source_round(config, None, 20))
            self.assertEqual(config['steps'], [step])
            self.assertEqual(config['sourceRoundContext'], previous)

    def test_failed_or_exceptional_persistence_rolls_back_transaction(self):
        def failed(): raise OSError('locked')
        for save in (lambda: False, failed):
            config = {'steps': [self.marker()], 'sourceRoundContext': {'index': 0, 'round': 6, 'startedAt': 5}}
            checkpoint = {'round': 6, 'nextStep': 2}
            before = deepcopy((config, checkpoint))
            def persist():
                checkpoint['nextStep'] = 3
                return save()
            drive_source_round(config, checkpoint, 20, persist)
            self.assertEqual((config, checkpoint), before)

    def test_resume_requires_latest_matching_consumed_command(self):
        original = [dict(action='play_once'), dict(action='source_round', round=6),
                    dict(action='play_once'), dict(action='source_round', round=7)]
        checkpoint = {'nextStep': 4, 'sourceRoundContext': {'index': 3, 'round': 7, 'startedAt': 20, 'extra': 'drop'},
                      'sourcePlay': {'index': 2, 'sentAt': 19}}
        restored = restore_source_round_context(original, checkpoint)
        self.assertNotIn('extra', restored['sourceRoundContext'])
        for key, change in (('sourcePlay', {'index': 0, 'sentAt': 1}),
                            ('sourceRoundContext', {'index': 1, 'round': 6, 'startedAt': 1}),
                            ('sourceRoundContext', {'index': 3, 'round': 8, 'startedAt': 1}),
                            ('sourcePlay', {'index': 2, 'sentAt': float('nan')})):
            bad = deepcopy(checkpoint); bad[key] = change
            with self.assertRaises(ValueError): restore_source_round_context(original, bad)
        bad = deepcopy(checkpoint); bad['nextStep'] = 3
        with self.assertRaises(ValueError): restore_source_round_context(original, bad)

    def test_canonical_parser_writer_normalizer_and_manual_pacing(self):
        source = (ROOT / 'autobtd6/helper.py').read_text(encoding='utf-8')
        start = source.index('    for line in configLines:'); end = source.index('        roundOffset =', start)
        env = dict(re=re, parse_autostart_command=parse_autostart_command,
                   configLines=['source round 7 after play'], newMapConfig={'steps': []}, keybinds={})
        exec('if True:\n' + source[start:end], env)
        step = normalize_action(env['newMapConfig']['steps'][0])
        self.assertEqual(step['round'], 7); self.assertTrue(step['afterPlay'])
        start = source.index('        elif action["action"] == "source_round":')
        end = source.index('        elif action["action"] == "play_once":', start)
        out = io.StringIO()
        exec(textwrap.dedent(source[start:end]).replace('elif ', 'if ', 1), dict(action=step, fp=out))
        self.assertEqual(out.getvalue(), 'source round 7 after play\n')
        self.assertFalse(pacing_allowed([step]))
        for round_value, after in ((True, False), (0, False), (7, 1)):
            with self.assertRaises(ValueError): normalize_action(dict(action='source_round', round=round_value, afterPlay=after))

    def test_source_abilities_wait_for_clock_legacy_abilities_unchanged(self):
        config = {'sourceRoundTiming': True}
        self.assertIsNone(source_round_anchor(config, 100))
        self.assertFalse(ability_ready({'action': 'ability', 'sourceTiming': True}, 110, None))
        self.assertTrue(ability_ready({'action': 'ability'}, 110, None))
        self.assertEqual(source_round_anchor({}, 100), 100)

    def test_actual_replay_frame_owner_withholds_busy_or_background_markers(self):
        tree = ast.parse((ROOT / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                      and 'drive_source_round' in ast.unparse(node) and 'autoInputFree' in ast.unparse(node.test)
                      and "'source_round'" in ast.unparse(node.test))
        loop = ast.For(target=ast.Name(id='_', ctx=ast.Store()), iter=ast.List(elts=[ast.Constant(0)], ctx=ast.Load()),
                       body=[branch], orelse=[])
        code = compile(ast.fix_missing_locations(ast.Module(body=[loop], type_ignores=[])), '<actual-source-owner>', 'exec')
        for free, foreground, consumes in ((True, True, True), (False, True, False), (True, False, False)):
            config = {'steps': [self.marker()]}; checkpoint = {'round': 6}; saved = []
            env = dict(mapConfig=config, routeCheckpoint=checkpoint, routeStepTotal=3,
                       autoInputFree=free, autoRoundKnown=True, screen=1, state=1,
                       Screen=SimpleNamespace(INGAME=1), windowed_input=SimpleNamespace(is_game_foreground=lambda: foreground),
                       time=SimpleNamespace(time=lambda: 20, sleep=lambda seconds: None),
                       drive_source_round=drive_source_round, customPrint=lambda message: None,
                       checkpointStepOffset=lambda steps, total: total-len(steps),
                       writeRouteCheckpoint=lambda *args: saved.append(deepcopy(checkpoint)) or True)
            exec(code, env)
            self.assertEqual(not config['steps'], consumes)
            self.assertEqual(len(saved), int(consumes))
            if consumes: self.assertEqual(saved[0]['nextStep'], 3)
        guard = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                     and ast.unparse(node.test) == "nextStepAction in ('set_autostart', 'source_round')")
        env = {'nextStepAction': 'source_round', 'nextStepDelayReady': True}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[guard], type_ignores=[])), '<generic-guard>', 'exec'), env)
        self.assertFalse(env['nextStepDelayReady'])


if __name__ == '__main__': unittest.main()
