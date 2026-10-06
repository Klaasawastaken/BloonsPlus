"""Pause switch observation only; synthetic off frames are not live evidence."""
import sys
import ast
from types import SimpleNamespace
from pathlib import Path
import unittest
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'autobtd6'))
from autostart_observation import observe_autostart


class AutostartObservation(unittest.TestCase):
    def reference(self, resolution='1920x1080'):
        frame = cv2.imread(str(ROOT / 'autobtd6/images' / resolution / 'ingame_paused.png'))
        self.assertIsNotNone(frame)
        return frame

    def test_real_on_calibrations(self):
        for resolution in ('1920x1080', '2560x1440'):
            frame = self.reference(resolution)
            result = observe_autostart(frame, frame)
            self.assertEqual(result['status'], 'known', (resolution, result))
            self.assertTrue(result['enabled'])
            self.assertTrue(result['pauseConfirmed'])

    def test_synthetic_off_switch_uses_existing_off_hints_control(self):
        reference = self.reference()
        frame = reference.copy()
        # Reuse the actual off Game Hints switch artwork at the Auto Start slot.
        # This checks decoding/geometry only; no real off screenshot is claimed.
        frame[275:338, 1259:1390] = reference[350:413, 1259:1390]
        result = observe_autostart(frame, reference)
        self.assertEqual(result['status'], 'known', result)
        self.assertFalse(result['enabled'])

    def test_ambiguous_or_missing_controls_send_no_coordinate(self):
        reference = self.reference()
        covered = reference.copy()
        covered[282:337, 1066:1248] = 0
        ambiguous = reference.copy()
        ambiguous[295:319, 1280:1303] = ambiguous[295:319, 1347:1370]
        for frame in (np.zeros_like(reference), covered, ambiguous, None,
                      np.zeros((201, 304, 3), np.uint8)):
            result = observe_autostart(frame, reference)
            self.assertEqual(result['status'], 'unknown', result)
            self.assertNotIn('position', result)

    def test_lime_or_green_without_pause_labels_is_not_a_pause_menu(self):
        reference = self.reference()
        frame = np.zeros_like(reference)
        frame[298:315, 1277:1320] = (0, 240, 120)
        frame[295:319, 1347:1370] = reference[295:319, 1347:1370]
        result = observe_autostart(frame, reference)
        self.assertFalse(result['pauseConfirmed'])
        self.assertNotIn('position', result)

    def test_pause_labels_and_switch_confidence_are_separate(self):
        reference = self.reference()
        frame = reference.copy()
        frame[295:319, 1280:1303] = frame[295:319, 1347:1370]
        result = observe_autostart(frame, reference)
        self.assertTrue(result['pauseConfirmed'])
        self.assertEqual(result['status'], 'unknown')
        self.assertNotIn('position', result)

    def test_actual_replay_pause_branch_requires_menu_evidence(self):
        tree = ast.parse((ROOT / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                      and node.body and isinstance(node.body[0], ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == 'pauseObservation'
                              for target in node.body[0].targets))
        code = compile(ast.fix_missing_locations(ast.Module(body=[branch], type_ignores=[])), '<actual-pause-branch>', 'exec')
        reference = self.reference()
        for frame, foreground, expected in ((np.zeros_like(reference), True, []),
                                             (reference, False, []),
                                             (reference, True, ['{Esc}'])):
            sent, messages = [], []
            scope = dict(lastScreen='paused', Screen=SimpleNamespace(INGAME_PAUSED='paused'),
                         screenshot=frame, comparisonImages={'screens': {'ingame_paused': reference}},
                         observe_autostart=observe_autostart, logStats=False,
                         windowed_input=SimpleNamespace(is_game_foreground=lambda: foreground),
                         customPrint=messages.append, sendKey=sent.append,
                         time=SimpleNamespace(sleep=lambda seconds: None))
            exec(code, scope)
            self.assertEqual(sent, expected)
            if not frame.any():
                self.assertTrue(any('withheld Esc' in message for message in messages))

    def test_scaled_frame_retains_location(self):
        reference = self.reference()
        result = observe_autostart(cv2.resize(reference, (2560, 1440)), reference)
        self.assertEqual(result['status'], 'known', result)
        self.assertEqual(result['position'], (1760, 409))


if __name__ == '__main__':
    unittest.main()
