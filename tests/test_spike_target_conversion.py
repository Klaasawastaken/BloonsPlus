"""Faithful Spike Factory Smart-target conversion without game input."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('spike_import',ROOT/'tools/import-public-routes.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SpikeTargets(unittest.TestCase):
    def route(self, bottom=2):
        route=m.Route('btd6bot','fixture.py','logs','hard')
        route.place('spike','spike',100,200)
        route.upgrade_to('spike',[0,0,bottom])
        return route

    def test_normal_to_smart_preserves_two_forward_presses_and_repeat_noop(self):
        route=self.route();before=len(route.lines)
        route.set_target('spike','smart')
        self.assertFalse(route.lossy)
        self.assertEqual(route.lines[before:],['retarget spike0','retarget spike0'])
        route.set_target('spike','smart')
        self.assertEqual(len(route.lines),before+2)

    def test_locked_or_uncertain_cycles_remain_lossy(self):
        for bottom,target in [(1,'smart'),(5,'smart'),(2,'set'),(2,'automatic')]:
            route=self.route(bottom);before=list(route.lines)
            route.set_target('spike',target)
            self.assertTrue(route.lossy,(bottom,target))
            self.assertEqual(route.lines,before)

    def test_candidate_creation_repeat_and_overwrite_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);plans=root/'plans';plans.mkdir();out=root/'routes';out.mkdir()
            (plans/'logsHardStandard.py').write_text('[Hero] -\n')
            route=self.route();route.set_target('spike','smart')
            original=out/'logs#hard#1920x1080.btd6';original.write_bytes(b'original recording')
            with patch.object(m,'BTD6BOT_PLANS',plans),patch.object(m,'PT',out),patch.object(m,'convert_btd6bot',return_value=route),patch.object(m,'validate',return_value={}),redirect_stdout(io.StringIO()):
                m.emit_spike_target_candidates()
                candidate=next(out.glob('*spike-target-preserved.btd6'));content=candidate.read_bytes()
                m.emit_spike_target_candidates();self.assertEqual(candidate.read_bytes(),content)
                self.assertEqual(original.read_bytes(),b'original recording')
                candidate.write_bytes(b'edited candidate')
                with self.assertRaisesRegex(RuntimeError,'Refusing to overwrite'):
                    m.emit_spike_target_candidates()

if __name__=='__main__':unittest.main()
