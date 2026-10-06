"""Read-only resume ledger validation; no game input or save edits."""
import sys
from pathlib import Path
from copy import deepcopy
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from game_runtime import GameState

class ResumeLedger(unittest.TestCase):
    def setUp(self):
        self.state = GameState({'map': 'logs', 'gamemode': 'hard'}, 'run')
        self.snapshot = {'runId': 'run', 'map': 'logs', 'mode': 'hard',
                         'towers': {'dart0': {'type': 'dart', 'position': [100, 200], 'upgrades': [2, 0, 0]}},
                         'events': [{'type': 'upgrade', 'tower': 'dart0', 'path': 0}],
                         'observations': [{'round': 12, 'cash': 1000}]}

    def test_valid_matching_ledger_is_copied(self):
        self.assertTrue(self.state.restore_ledger(self.snapshot))
        self.snapshot['towers']['dart0']['upgrades'][0] = 5
        self.assertEqual(self.state.towers['dart0']['upgrades'], [2, 0, 0])

    def test_other_run_is_not_restored(self):
        for field in ('runId', 'map', 'mode'):
            data = deepcopy(self.snapshot)
            data[field] = 'other'
            self.assertFalse(self.state.restore_ledger(data))
            self.assertEqual(self.state.towers, {})

    def test_corrupt_shapes_do_not_partially_replace_existing_state(self):
        self.state.restore_ledger(self.snapshot)
        original = deepcopy(self.state.towers)
        malformed = [[], None, {'towers': []}, {'events': {}}, {'observations': [None]},
                     {'towers': {'dart0': None}}, {'events': [None]}]
        for changes in malformed:
            data = {**deepcopy(self.snapshot), **changes} if isinstance(changes, dict) else changes
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.state.restore_ledger(data)
            self.assertEqual(self.state.towers, original)

    def test_invalid_tower_paths_and_positions_are_rejected(self):
        for field, value in [('upgrades', [True, 0, 0]), ('upgrades', [6, 0, 0]),
                             ('upgrades', [3, 3, 0]), ('upgrades', [1, 1, 1]),
                             ('position', [True, 200]), ('position', [-1, 200]), ('type', None)]:
            data = deepcopy(self.snapshot)
            data['towers']['dart0'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.state.restore_ledger(data)
            self.assertEqual(self.state.towers, {})

if __name__ == '__main__':
    unittest.main()
