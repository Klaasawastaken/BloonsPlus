"""Exercise the actual replay reconciliation branch without launching the game."""
import ast
from pathlib import Path
import unittest


class UpgradeQueue(unittest.TestCase):
    def reconcile(self, status, attempts=0, money=22100):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                      and 'lastIterationCost > 0' in ast.unparse(node.test)
                      and 'lastIterationAction' in ast.unparse(node.test))
        action = dict(action='upgrade', name='heli0', path=0, selectionAttempts=attempts,
                      upgradeObservation=dict(status=status, before=[3, 2, 0]))
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


if __name__ == '__main__':
    unittest.main()
