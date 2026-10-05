"""Exercise the actual replay reconciliation branch without launching the game."""
import ast
from pathlib import Path
import unittest
from types import SimpleNamespace


class UpgradeQueue(unittest.TestCase):
    def test_owned_retry_advances_with_zero_cash_before_purchase_gate(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                      and "nextStep.pop('resumeUpgradeProbe', False)" in ast.unparse(node.test))
        action = dict(action='upgrade', name='heli0', path=0, pos=(10, 20), cost=20000,
                      expectedUpgradeTiers=[4, 0, 2], resumeUpgradeProbe=True)
        clicks, reached = [], []
        env = dict(nextStep=action, mapConfig=dict(steps=[action, dict(action='next')]),
                   pyautogui=SimpleNamespace(click=lambda *a, **kw: clicks.append(kw)),
                   time=SimpleNamespace(sleep=lambda _: None), currentGameState=None,
                   routeCheckpoint=None, currentValues={'money': 0}, customPrint=lambda _: None,
                   probe_owned_upgrade=lambda *a, **kw: {'status': 'confirmed', 'after': [4, 0, 2]},
                   reached=reached)
        # A confirmed probe continues the replay loop before any cash-gated input.
        loop = ast.For(target=ast.Name(id='_iteration', ctx=ast.Store()),
                       iter=ast.List(elts=[ast.Constant(0)], ctx=ast.Load()),
                       body=[branch, ast.parse('reached.append("cash gate")').body[0]], orelse=[])
        exec(compile(ast.fix_missing_locations(ast.Module(body=[loop], type_ignores=[])), '<probe>', 'exec'), env)
        self.assertEqual(env['mapConfig']['steps'], [dict(action='next')])
        self.assertEqual(reached, [])
        self.assertEqual(clicks, [{'button': 'right'}, {'button': 'right'}])
        self.assertEqual(env['lastIterationCost'], 0)

    def reconcile(self, status, attempts=0, money=22100, target=None):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                      and 'lastIterationCost > 0' in ast.unparse(node.test)
                      and 'lastIterationAction' in ast.unparse(node.test))
        action = dict(action='upgrade', name='heli0', path=0, selectionAttempts=attempts,
                      upgradeObservation=dict(status=status, before=[3, 2, 0]))
        if target is not None:
            action['expectedUpgradeTiers'] = target
        self.confirmations = []
        env = dict(lastIterationAction=action, lastIterationBalance=22000,
                   currentValues=dict(money=money, round=52), lastIterationCost=21170,
                   currentGameState=None, mapConfig=dict(steps=[dict(action='next')]),
                   routeCheckpoint=None, customPrint=lambda *_: None,
                   updateUpgradeMemory=lambda *args: self.confirmations.append(args), upgradeRunId='test')
        exec(compile(ast.Module(body=[branch], type_ignores=[]), '<reconciliation>', 'exec'), env)
        return env['mapConfig']['steps']

    def test_unselected_upgrade_retries_before_dependents(self):
        steps = self.reconcile('unselected')
        self.assertEqual(steps[0]['action'], 'upgrade')
        self.assertEqual(steps[0]['selectionAttempts'], 1)
        self.assertNotIn('upgradeObservation', steps[0])

    def test_unchanged_preserves_exact_target(self):
        self.assertEqual(self.reconcile('unchanged')[0]['expectedUpgradeTiers'], [4, 2, 0])

    def test_unknown_and_exhausted_do_not_blindly_retry(self):
        for status, attempts in [('unknown', 0), ('unselected', 2), ('confirmed', 0)]:
            self.assertEqual(self.reconcile(status, attempts), [dict(action='next')])

    def test_cash_drop_does_not_confirm_unreadable_upgrade(self):
        self.reconcile('unknown', money=830)
        self.assertEqual(self.confirmations, [])

    def test_visible_tiers_confirm_despite_income(self):
        self.reconcile('confirmed', money=22100)
        self.assertEqual(len(self.confirmations), 1)

    def test_unknown_with_exact_intent_rechecks_before_dependents(self):
        steps = self.reconcile('unknown', target=[4, 2, 0])
        self.assertEqual(steps[0]['action'], 'upgrade')
        self.assertEqual(steps[0]['expectedUpgradeTiers'], [4, 2, 0])
        self.assertNotIn('upgradeObservation', steps[0])
        self.assertTrue(steps[0]['resumeUpgradeProbe'])
        self.assertEqual(self.reconcile('unknown', attempts=2, target=[4, 2, 0]), [dict(action='next')])

    def test_wrong_panel_only_retries_with_exact_intent(self):
        self.assertEqual(self.reconcile('unexpected'), [dict(action='next')])
        steps = self.reconcile('unexpected', target=[4, 2, 0])
        self.assertEqual(steps[0]['expectedUpgradeTiers'], [4, 2, 0])
        self.assertTrue(steps[0]['resumeUpgradeProbe'])
        self.assertEqual(steps[0]['selectionAttempts'], 1)
        self.assertEqual(self.reconcile('unexpected', attempts=2, target=[4, 2, 0]), [dict(action='next')])


if __name__ == '__main__':
    unittest.main()
