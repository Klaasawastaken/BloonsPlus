"""Exercise replay life reconciliation without game input."""
import ast
from pathlib import Path
import unittest


class LivesRecovery(unittest.TestCase):
    def run_readings(self, readings, alternatives=True):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                      and ast.unparse(n.test) == 'livesReading > 0')
        code = compile(ast.Module(body=[branch], type_ignores=[]), '<lives>', 'exec')
        env = dict(startLives=100, lastLives=82, pendingLives=None, pendingLivesFrames=0,
                   lowLivesFrames=0, emergencySpend=False, currentGameState=None,
                   currentValues={'round': 22}, customPrint=lambda *_: None, images=[None])
        for reading in readings:
            env['livesReading'] = reading
            env['custom_ocr'] = lambda *a, **kw: str(reading if alternatives else 82)
            exec(code, env)
        return env

    def test_sustained_large_loss_resynchronizes(self):
        self.assertEqual(self.run_readings([41, 40, 38])['lastLives'], 38)

    def test_single_low_glitch_does_not_resynchronize(self):
        self.assertEqual(self.run_readings([6, 82, 82])['lastLives'], 82)

    def test_disagreeing_masks_do_not_confirm_large_drop(self):
        self.assertEqual(self.run_readings([6, 6, 6], False)['lastLives'], 82)

    def test_normal_small_loss_still_confirms(self):
        self.assertEqual(self.run_readings([79, 79])['lastLives'], 79)

    def test_large_drop_can_trigger_emergency(self):
        self.assertTrue(self.run_readings([41, 40, 38, 38, 38])['emergencySpend'])
