import ast, io, json, re, sys, textwrap, unittest
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'autobtd6'))
from play_once import play_once_ready, restore_play_once
from resume_recovery import restore_action, resumable_round_start
from autostart_control import parse_autostart_command
from game_runtime import normalize_action, GameState
from purchase_pacing import pacing_allowed

class PlayOnceTests(unittest.TestCase):
    def step(self):return dict(action='play_once',key='F8',cost=0,routeStepIndex=4)

    def test_paused_origin_sends_once_and_accepts_either_retained_speed(self):
        for speed in ('slow','fast'):
            step=self.step(); calls=[]
            self.assertEqual(play_once_ready(step,10,'paused',6,True,calls.append),(False,True))
            self.assertEqual(play_once_ready(step,10.2,speed,6,True,calls.append),(False,False))
            self.assertEqual(play_once_ready(step,11,speed,6,True,calls.append),(True,False))
            self.assertEqual(calls,['F8']);self.assertTrue(step['playStateConfirmed'])

    def test_running_origin_requires_opposite_speed_not_merely_later_round(self):
        for origin,target in (('slow','fast'),('fast','slow')):
            step=self.step();calls=[]
            play_once_ready(step,10,origin,20,True,calls.append)
            for now in (11,20,100):
                self.assertEqual(play_once_ready(step,now,origin,21,True,calls.append),(False,False))
            self.assertEqual(play_once_ready(step,101,target,21,True,calls.append),(True,False))
            self.assertEqual(calls,['F8'])

    def test_short_round_can_finish_before_next_frame(self):
        step=self.step();play_once_ready(step,10,'paused',6,True,lambda key:None)
        self.assertEqual(play_once_ready(step,11,'paused',7,True,self.fail),(True,False))
        self.assertIsNone(step['speed'])

    def test_running_input_completed_round_before_speed_confirmation(self):
        # Live failure: the receipt began on fast at round 13; the next
        # observable frame was paused at 14, so opposite speed was gone.
        for origin in ('fast', 'slow'):
            step=self.step(); calls=[]; messages=[]
            play_once_ready(step,10,origin,13,True,calls.append)
            self.assertEqual(play_once_ready(step,10.2,'paused',14,True,self.fail),(False,False))
            self.assertEqual(play_once_ready(step,11,'paused',14,True,self.fail,report=messages.append),(True,False))
            self.assertEqual(calls,['F8'])
            self.assertTrue(step['playStateConfirmed'])
            self.assertIsNone(step['speed'])
            self.assertTrue(any('round boundary' in message for message in messages))

    def test_running_receipt_rejects_pause_without_round_boundary_and_survives_resume(self):
        step=self.step();play_once_ready(step,10,'fast',13,True,lambda key:None)
        restored=restore_action(self.step(),json.loads(json.dumps(step)))
        for round_ in (12,13):
            self.assertEqual(play_once_ready(restored,11,'paused',round_,True,self.fail),(False,False))
        self.assertEqual(play_once_ready(restored,12,'paused',14,False,self.fail),(False,False))
        self.assertEqual(play_once_ready(restored,12,None,14,True,self.fail),(False,False))
        self.assertEqual(play_once_ready(restored,12,'paused',14,True,self.fail),(True,False))

    def test_unknown_busy_unreadable_or_unbound_withholds_input(self):
        for state,round_,free in ((None,6,True),('slow',None,True),('paused',True,True),('slow',6,False)):
            self.assertEqual(play_once_ready(self.step(),10,state,round_,free,self.fail),(False,False))
        step=self.step();step['key']=None
        self.assertEqual(play_once_ready(step,10,'slow',6,True,self.fail),(False,False))

    def test_checkpoint_failure_and_transport_exception(self):
        step=self.step()
        self.assertEqual(play_once_ready(step,10,'slow',6,True,self.fail,lambda:False),(False,False))
        self.assertNotIn('playOncePending',step)
        def broken(key):raise OSError('transport')
        with self.assertRaises(OSError):play_once_ready(step,11,'slow',6,True,broken)
        self.assertIn('playOncePending',step)
        self.assertEqual(play_once_ready(step,15,'slow',6,True,self.fail),(False,False))

    def test_resume_rebinds_and_observes_without_repeating_key(self):
        source=self.step(); saved=self.step()
        play_once_ready(saved,10,'slow',6,True,lambda key:None)
        source['key']='F9'; saved['playOncePending']['key']='untrusted';saved['key']='untrusted'
        restored=restore_action(source,json.loads(json.dumps(saved)))
        self.assertEqual(restored['key'],'F9');self.assertNotIn('key',restored['playOncePending'])
        self.assertEqual(play_once_ready(restored,12,'fast',6,True,self.fail),(True,False))
        checkpoint=dict(status='pending',pendingAction='play_once',nextStep=4,remainingSteps=[saved])
        self.assertTrue(resumable_round_start(checkpoint))
        for field,value in (('from','bad'),('sentAt',True),('sentAt',float('nan')),('round',True),('round',0)):
            bad=deepcopy(saved);bad['playOncePending'][field]=value
            with self.assertRaises(ValueError):restore_action(source,bad)
            self.assertFalse(resumable_round_start(dict(checkpoint,remainingSteps=[bad])))

    def test_explicit_resume_accepts_stopped_round_control_but_not_pending_purchase(self):
        step=self.step();play_once_ready(step,10,'fast',13,True,lambda key:None)
        checkpoint=dict(status='paused',pendingAction=None,nextStep=4,remainingSteps=[step])
        self.assertTrue(resumable_round_start(checkpoint))
        self.assertEqual(play_once_ready(restore_action(self.step(),step),12,'paused',14,True,self.fail),(True,False))
        for change in ({'nextStep':5}, {'remainingSteps':[self.step()]},
                       {'pendingAction':'upgrade'}, {'remainingSteps':[dict(action='upgrade',routeStepIndex=4)]}):
            self.assertFalse(resumable_round_start(dict(checkpoint,**change)))
        broken=deepcopy(step);broken['playOncePending']['sentAt']=True
        self.assertFalse(resumable_round_start(dict(checkpoint,remainingSteps=[broken])))
        for action in ('start_round','speed_toggle'):
            control=dict(action=action,routeStepIndex=4,speed='slow',speedToggleFrom='fast',
                         roundStartPending=dict(sentAt=10,**{'from':'fast'}))
            self.assertTrue(resumable_round_start(dict(checkpoint,remainingSteps=[control])))
            control['roundStartPending']['sentAt']=True
            self.assertFalse(resumable_round_start(dict(checkpoint,remainingSteps=[control])))

    def test_backward_clock_rebases_without_input_or_losing_failed_save(self):
        step=self.step();play_once_ready(step,20,'slow',6,True,lambda key:None)
        self.assertEqual(play_once_ready(step,10,'fast',6,True,self.fail,lambda:False),(False,False))
        self.assertEqual(step['playOncePending']['sentAt'],20)
        self.assertEqual(play_once_ready(step,10,'fast',6,True,self.fail),(False,False))
        self.assertEqual(play_once_ready(step,11,'fast',6,True,self.fail),(True,False))

    def test_actual_parser_writer_ledger_and_pacing(self):
        source=(ROOT/'autobtd6/helper.py').read_text(encoding='utf-8')
        start=source.index('    for line in configLines:');end=source.index('        roundOffset =',start)
        env=dict(re=re,parse_autostart_command=parse_autostart_command,configLines=['play once'],
                 newMapConfig={'steps':[]},keybinds={'others':{'play':'F8'}})
        exec('if True:\n'+source[start:end],env)
        step=normalize_action(env['newMapConfig']['steps'][0]);self.assertEqual(step['key'],'F8')
        start=source.index('        elif action["action"] == "play_once":');end=source.index('        elif action["action"] == "await_round":',start)
        out=io.StringIO();exec(textwrap.dedent(source[start:end]).replace('elif ','if ',1),dict(action=step,fp=out))
        self.assertEqual(out.getvalue(),'play once\n');self.assertFalse(pacing_allowed([step]))
        state=GameState({},'offline');state.record_issued_action(step)
        self.assertEqual(state.events[-1]['status'],'issued-unverified')
        play_once_ready(step,10,'slow',6,True,lambda key:None);play_once_ready(step,11,'fast',6,True,self.fail)
        state.record_issued_action(step);self.assertEqual(state.events[-1]['status'],'play-state-confirmed')

    def test_actual_replay_branch_owns_round_input(self):
        source=(ROOT/'autobtd6/replay.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        branch=next(node for node in ast.walk(tree) if isinstance(node,ast.If)
                    and isinstance(node.test,ast.BoolOp) and ast.unparse(node.test).startswith("nextStepAction in ('play_once', 'play_twice', 'start_round', 'speed_toggle')"))
        code=compile(ast.fix_missing_locations(ast.Module(body=[branch],type_ignores=[])),'<actual-play-input>','exec')
        sent=[]; step=self.step()
        env=dict(nextStepAction='play_once',nextStepDelayReady=True,nextStep=step,
                 currentValues={'round':6},screenshot='screen',imageAreas={'compare':{'game_state':None}},
                 comparisonImages={'game_state':dict(game_playing_fast=.4,game_playing_slow=0.,game_paused=.7)},
                 cv2=SimpleNamespace(TM_SQDIFF_NORMED=1,matchTemplate=lambda image,reference,mode:np.array([[reference]])),
                 cutImage=lambda image,area:image,routeCheckpoint={'status':'ready'},mapConfig={'steps':[step]},
                 writeRouteCheckpoint=lambda *args:sent.append('save') or True,
                 time=SimpleNamespace(time=lambda:10),skippingIteration=False,heldPlacement=False,routeActionExecuted=False,
                 sendKey=lambda key:sent.append(key),customPrint=lambda message:None,play_once_ready=play_once_ready,
                 playToggleIssued=False)
        exec(code,env)
        self.assertEqual(sent,['save','F8']);self.assertFalse(env['nextStepDelayReady'])
        self.assertTrue(env['playToggleIssued']);self.assertTrue(env['routeActionExecuted'])

    def test_actual_startup_gate_waits_for_planned_single_play(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        assignment=next(node for node in ast.walk(tree) if isinstance(node,ast.Assign)
                        and any(isinstance(target,ast.Name) and target.id=='startupRoundStartPending' for target in node.targets))
        code=compile(ast.fix_missing_locations(ast.Module(body=[assignment],type_ignores=[])),'<actual-startup>','exec')
        for completed,steps,expected in ((False,[self.step()],True),(True,[self.step()],False),(False,[{'action':'place'}],False)):
            env={'mapConfig':{'steps':steps,'roundStartCompleted':completed}}
            exec(code,env);self.assertEqual(env['startupRoundStartPending'],expected)

if __name__=='__main__':unittest.main()
