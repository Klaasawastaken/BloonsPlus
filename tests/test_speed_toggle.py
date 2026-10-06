"""Observed relative controls; no game input or save access."""
import sys, io, re, textwrap
from pathlib import Path
import unittest
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'autobtd6'))
from route_timing import round_start_ready
from resume_recovery import restore_action, resumable_round_start
from game_runtime import normalize_action, GameState


class RelativeSpeed(unittest.TestCase):
    def test_observed_transitions_and_confirmation(self):
        for initial, target in [('slow','fast'),('fast','slow'),('paused','slow')]:
            step = dict(action='speed_toggle', key='F8')
            inputs = []
            self.assertEqual(round_start_ready(step,10,initial,True,inputs.append),(False,True))
            self.assertEqual(step['speed'],target)
            self.assertEqual(inputs,['F8'])
            self.assertEqual(round_start_ready(step,10.5,target,True,inputs.append),(False,False))
            self.assertEqual(round_start_ready(step,11,target,True,inputs.append),(True,False))
            self.assertEqual(inputs,['F8'],'Observing the target must not toggle it back')

    def test_unknown_busy_unbound_and_failed_persistence_send_nothing(self):
        for state, free in [(None,True),('unknown',True),('slow',False)]:
            step = dict(action='speed_toggle', key='F8')
            self.assertEqual(round_start_ready(step,10,state,free,self.fail),(False,False))
            self.assertNotIn('speed',step)
        step = dict(action='speed_toggle',key='F8')
        self.assertEqual(round_start_ready(step,10,'slow',True,self.fail,persist=lambda:False),(False,False))
        self.assertNotIn('roundStartPending',step)
        self.assertEqual(round_start_ready(dict(action='speed_toggle',key=None),10,'slow',True,self.fail),(False,False))

    def test_resume_preserves_relative_intent_with_fresh_binding(self):
        source = dict(action='speed_toggle',key='F9',routeStepIndex=4)
        saved = dict(source,key='F8')
        round_start_ready(saved,10,'slow',True,lambda _:None)
        resumed = restore_action(source,saved)
        self.assertEqual(resumed['key'],'F9')
        self.assertEqual(round_start_ready(resumed,12,'fast',True,self.fail),(True,False))
        checkpoint = dict(status='pending',pendingAction='speed_toggle',nextStep=4,remainingSteps=[saved])
        self.assertTrue(resumable_round_start(checkpoint))
        for field, value in [('speed','slow'),('speedToggleFrom','invalid'),('routeStepIndex',3)]:
            bad=deepcopy(checkpoint);bad['remainingSteps'][0][field]=value
            self.assertFalse(resumable_round_start(bad))
        with self.assertRaises(ValueError):
            restore_action(source,dict(saved,speed='slow'))

    def test_round_ending_does_not_erase_original_toggle_intent(self):
        source=dict(action='speed_toggle',key='F9')
        saved=dict(source)
        round_start_ready(saved,10,'slow',True,lambda _:None)
        round_start_ready(saved,13,'paused',True,lambda _:None)
        resumed=restore_action(source,saved)
        self.assertEqual(resumed['speed'],'fast')
        self.assertEqual(resumed['speedToggleFrom'],'slow')
        self.assertEqual(round_start_ready(resumed,15,'fast',True,self.fail),(True,False))

    def test_parser_recorder_and_action_contract(self):
        source=(ROOT/'autobtd6/helper.py').read_text()
        start=source.index('    for line in configLines:')
        end=source.index('        roundOffset =',start)
        ctx=dict(re=re,configLines=['change speed'],newMapConfig={'steps':[]},keybinds={'others':{'play':'F8'}})
        exec('if True:\n'+source[start:end],ctx)
        self.assertEqual(normalize_action(ctx['newMapConfig']['steps'][0])['action'],'speed_toggle')
        start=source.index('        elif action["action"] == "speed_toggle":')
        end=source.index('        elif action["action"] == "await_round":',start)
        output=io.StringIO()
        exec(textwrap.dedent(source[start:end]).replace('elif ','if ',1),dict(action={'action':'speed_toggle'},fp=output))
        self.assertEqual(output.getvalue(),'change speed\n')
        state=GameState({},'offline')
        state.record_issued_action(dict(action='speed_toggle',speed='slow',playStateConfirmed=True))
        self.assertEqual(state.speed,'slow')
        self.assertEqual(state.speed_status,'play-state-confirmed')


if __name__=='__main__': unittest.main()
