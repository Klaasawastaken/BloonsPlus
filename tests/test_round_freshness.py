"""Round read freshness does not advance when OCR is unreadable."""
import sys
from pathlib import Path
from unittest.mock import patch
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from game_runtime import GameState

class RoundFreshness(unittest.TestCase):
    def test_unreadable_frame_keeps_last_round_and_original_read_time(self):
        state = GameState({'map': 'infernal', 'gamemode': 'reverse'}, 'run')
        with patch('game_runtime.time.strftime', return_value='2026-10-06T05:00:00Z'):
            state.observe(1000, 17, 'INGAME')
        with patch('game_runtime.time.strftime', return_value='2026-10-06T05:02:00Z'):
            state.observe(2000, -1, 'INGAME')
        snapshot = state.to_dict()
        self.assertEqual(snapshot['round'], 17)
        self.assertEqual(snapshot['roundObservedAt'], '2026-10-06T05:00:00Z')
        self.assertEqual(snapshot['observations'][-1]['roundObservedAt'], '2026-10-06T05:00:00Z')
        self.assertEqual(snapshot['updatedAt'], '2026-10-06T05:02:00Z')

    def test_no_round_has_no_read_time_and_bool_is_not_a_counter(self):
        state = GameState({'map': 'logs', 'gamemode': 'easy'}, 'run')
        state.observe(round_number=True)
        self.assertIsNone(state.to_dict()['round'])
        self.assertIsNone(state.to_dict()['roundObservedAt'])

if __name__ == '__main__':
    unittest.main()
