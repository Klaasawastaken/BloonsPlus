import ast, io, re, sys, textwrap, unittest
import numpy as np
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'autobtd6'))
from play_sequence import play_sequence_ready, restore_play_sequence
from resume_recovery import restore_action, resumable_round_start
from game_runtime import normalize_action, GameState
from purchase_pacing import pacing_allowed
from autostart_control import parse_autostart_command
from source_round import restore_source_round_context

class PlaySequenceTests(unittest.TestCase):
    def step(self):return dict(action='play_twice',key='F8',cost=0,routeStepIndex=4)

    def test_native_spacing_observes_first_then_second_transition(self):
        for origin,first,target in (('paused','slow','fast'),('slow','fast','slow'),('fast','slow','fast')):
            step=self.step();calls=[];clock=[10]
            def sleep(delay):calls.append(('sleep',delay));clock[0]+=delay
            sent=lambda key:calls.append(('press',clock[0],key))
            ready=play_sequence_ready(step,10,origin,6,True,sent,observe=lambda:{'foreground':True,'state':first,'round':6},sleep=sleep,clock=lambda:clock[0])
            self.assertEqual(ready,(False,True))
            self.assertEqual([item[0] for item in calls],['press','sleep','press'])
            self.assertAlmostEqual(calls[2][1]-calls[0][1],.2)
            self.assertEqual(play_sequence_ready(step,10.4,target,6,True,sent),(False,False))
            self.assertEqual(play_sequence_ready(step,11.3,target,6,True,sent),(True,False))
            self.assertEqual(step['speed'],target);self.assertEqual(len(calls),3)

    def test_resume_each_phase_does_not_repeat_prior_key(self):
        step=self.step();calls=[]
        play_sequence_ready(step,10,'slow',6,True,calls.append)
        restored=restore_action(dict(self.step(),key='new-key'),step)
        self.assertEqual(play_sequence_ready(restored,11,'fast',6,True,calls.append),(False,True))
        self.assertEqual(calls,['F8','new-key'])
        restored=restore_action(self.step(),restored)
        self.assertEqual(play_sequence_ready(restored,13,'slow',6,True,calls.append),(True,False))
        self.assertEqual(calls,['F8','new-key'])
        checkpoint=dict(status='pending',pendingAction='play_twice',nextStep=4,remainingSteps=[restored])
        self.assertTrue(resumable_round_start(checkpoint))

    def test_first_or_second_ambiguous_receipt_never_repeats(self):
        step=self.step();calls=[]
        play_sequence_ready(step,10,'slow',6,True,calls.append)
        for now in (11,20,100):self.assertEqual(play_sequence_ready(step,now,'slow',7,True,calls.append),(False,False))
        self.assertEqual(calls,['F8'])
        play_sequence_ready(step,101,'fast',7,True,calls.append)
        for now in (102,200):self.assertEqual(play_sequence_ready(step,now,'fast',8,True,calls.append),(False,False))
        self.assertEqual(calls,['F8','F8'])

    def test_busy_unknown_unbound_or_foreground_loss_withholds_input(self):
        for state,free,number in ((None,True,6),('slow',False,6),('slow',True,True),('slow',True,0)):
            step=self.step();calls=[];play_sequence_ready(step,10,state,number,free,calls.append)
            self.assertEqual(calls,[])
        for fresh in ({'foreground':False,'state':'fast','round':6},{'foreground':True,'state':None,'round':6}):
            step=self.step();calls=[]
            play_sequence_ready(step,10,'slow',6,True,calls.append,observe=lambda:fresh,sleep=lambda delay:None,clock=lambda:11)
            self.assertEqual(calls,['F8']);self.assertEqual(step['sequencePending']['phase'],'first')

    def test_failed_saves_rollback_without_unsaved_inputs(self):
        def failed():raise OSError('locked')
        for save in (lambda:False,failed):
            step=self.step();calls=[]
            play_sequence_ready(step,10,'slow',6,True,calls.append,persist=save)
            self.assertEqual(calls,[]);self.assertNotIn('sequencePending',step)
            play_sequence_ready(step,10,'slow',6,True,calls.append)
            before=deepcopy(step)
            play_sequence_ready(step,11,'fast',6,True,calls.append,persist=save)
            self.assertEqual(step,before);self.assertEqual(calls,['F8'])

    def test_checkpoint_metadata_rejects_impossible_transition_and_wrong_index(self):
        step=self.step();play_sequence_ready(step,10,'slow',6,True,lambda key:None)
        for change in ({'phase':'third'},{'sentAt':float('nan')},{'round':True},
                       {'phase':'second','firstState':'slow'}):
            bad=deepcopy(step);bad['sequencePending'].update(change)
            with self.assertRaises(ValueError):restore_play_sequence(self.step(),bad)
        cp=dict(status='pending',pendingAction='play_twice',nextStep=3,remainingSteps=[step])
        self.assertFalse(resumable_round_start(cp))
        original=[dict(action='play_once'),dict(action='play_twice')]
        restored=restore_source_round_context(original,dict(nextStep=2,sourcePlay={'index':1,'sentAt':10}))
        self.assertEqual(restored['sourcePlay']['index'],1)
        with self.assertRaises(ValueError):restore_source_round_context(original,dict(nextStep=2,sourcePlay={'index':0,'sentAt':10}))

    def test_actual_parser_writer_ledger_and_pacing(self):
        source=(ROOT/'autobtd6/helper.py').read_text(encoding='utf-8')
        start=source.index('    for line in configLines:');end=source.index('        roundOffset =',start)
        env=dict(re=re,parse_autostart_command=parse_autostart_command,configLines=['play twice'],newMapConfig={'steps':[]},keybinds={'others':{'play':'F8'}})
        exec('if True:\n'+source[start:end],env);step=normalize_action(env['newMapConfig']['steps'][0])
        start=source.index('        elif action["action"] == "play_twice":');end=source.index('        elif action["action"] == "play_once":',start)
        out=io.StringIO();exec(textwrap.dedent(source[start:end]).replace('elif ','if ',1),dict(action=step,fp=out))
        self.assertEqual(out.getvalue(),'play twice\n');self.assertFalse(pacing_allowed([step]))
        state=GameState({},'offline');state.record_issued_action(step)
        self.assertEqual(state.events[-1]['status'],'issued-unverified')
        play_sequence_ready(step,10,'slow',6,True,lambda key:None)
        play_sequence_ready(step,11,'fast',6,True,lambda key:None)
        play_sequence_ready(step,13,'slow',6,True,lambda key:None)
        state.record_issued_action(step);self.assertEqual(state.events[-1]['status'],'play-state-confirmed')

    def test_actual_replay_branch_owns_both_inputs_and_checks_native_frame(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch=next(node for node in ast.walk(tree) if isinstance(node,ast.If)
                    and isinstance(node.test,ast.BoolOp) and ast.unparse(node.test).startswith("nextStepAction in ('play_once', 'play_twice'"))
        code=compile(ast.fix_missing_locations(ast.Module(body=[branch],type_ignores=[])),'<actual-sequence-owner>','exec')
        for foreground,screen,keys in ((True,1,2),(False,1,1),(True,2,1)):
            step=self.step();sent=[];clock=[10]
            refs=dict(game_playing_fast=.4,game_playing_slow=0.,game_paused=.7)
            def press(key):
                sent.append(key)
                refs.update(game_playing_fast=0.,game_playing_slow=.4)
            env=dict(nextStepAction='play_twice',nextStepDelayReady=True,nextStep=step,
                     currentValues={'round':6},screenshot=np.zeros((2,2,3)),imageAreas={'compare':{'game_state':None}},
                     comparisonImages={'game_state':refs},np=np,
                     cv2=SimpleNamespace(TM_SQDIFF_NORMED=1,matchTemplate=lambda image,reference,mode:np.array([[reference]])),
                     cutImage=lambda image,area:image,routeCheckpoint={},mapConfig={'steps':[step]},
                     writeRouteCheckpoint=lambda *args:sent.append('save') or True,
                     time=SimpleNamespace(time=lambda:clock[0],sleep=lambda delay:clock.__setitem__(0,clock[0]+delay)),
                     windowed_input=SimpleNamespace(is_game_foreground=lambda:foreground),
                     pyautogui=SimpleNamespace(screenshot=lambda:np.zeros((2,2,3))),
                     recognizeScreen=lambda *args:screen,Screen=SimpleNamespace(INGAME=1),
                     skippingIteration=False,heldPlacement=False,routeActionExecuted=False,
                     sendKey=press,customPrint=lambda message:None,play_sequence_ready=play_sequence_ready,
                     playToggleIssued=False)
            exec(code,env)
            self.assertEqual(sent.count('F8'),keys)
            self.assertEqual(sent.count('save'),keys)
            self.assertFalse(env['nextStepDelayReady']);self.assertTrue(env['routeActionExecuted'])
            self.assertTrue(env['playToggleIssued'])

if __name__=='__main__':unittest.main()
