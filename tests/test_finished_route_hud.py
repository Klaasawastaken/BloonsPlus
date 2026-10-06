"""Finished-route HUD recovery: injected captures/clicks, no gameplay input."""
import ast
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'autobtd6'))
import upgrade_observation as observation

class FinishedRouteHud(unittest.TestCase):
    def recover(self, **kwargs):
        function=getattr(observation,'recover_finished_route_hud',None)
        self.assertTrue(callable(function),'Finished-route overlay recovery is missing')
        return function(**kwargs)

    def test_actual_replay_enters_recovery_when_final_action_is_done(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch=next(node for node in ast.walk(tree) if isinstance(node,ast.If)
            and any(isinstance(child,ast.Assign) and any(isinstance(target,ast.Name)
                and target.id=='recognitionErrorSignature' for target in child.targets) for child in node.body))
        env={'currentValues':{'money':92000,'round':-1},'cashRequiredForNext':False,
             'roundRequiredForNext':False,'finishedRouteHudMissing':True}
        self.assertTrue(eval(compile(ast.Expression(branch.test),'<actual-HUD-gate>','eval'),env))

    def test_waits_for_fresh_frame_then_closes_observed_panel_twice(self):
        frame=np.zeros((1080,1920,3),np.uint8); events=[]
        def capture(): events.append('capture'); return frame
        with patch.object(observation,'held_placement_visible',return_value=False), \
             patch.object(observation,'resolve_hud_panels',return_value=(False,True)):
            self.assertTrue(self.recover(capture=capture,click=lambda p:events.append(('click',p)),
                wait=lambda s:events.append(('wait',s)),input_ready=lambda f:f is None or f is frame))
        self.assertEqual(events,[('wait',1.0),'capture',('click',(960,540)),('wait',.2),'capture',
                                 ('click',(960,540)),('wait',1.0)])

    def test_pending_input_or_changed_screen_produces_no_click(self):
        for blocked_at in (1,2,3):
            events=[];calls=[0];frame=np.zeros((540,960,3),np.uint8)
            def ready(f):
                calls[0]+=1
                return calls[0]!=blocked_at
            with patch.object(observation,'held_placement_visible',return_value=False), \
                 patch.object(observation,'resolve_hud_panels',return_value=(True,False)):
                result=self.recover(capture=lambda:frame,click=events.append,wait=lambda _:None,input_ready=ready)
            self.assertEqual(events,[] if blocked_at<3 else [(480,270)])
            self.assertEqual(result,blocked_at==3)

    def test_second_click_needs_a_new_ingame_capture(self):
        ingame=np.zeros((540,960,3),np.uint8)
        changed=np.ones_like(ingame)
        for final in (changed,None):
            frames=iter([ingame,final]);captures=[];clicks=[]
            def capture():
                value=next(frames);captures.append(value);return value
            with patch.object(observation,'held_placement_visible',return_value=False), \
                 patch.object(observation,'resolve_hud_panels',return_value=(False,True)):
                issued=self.recover(capture=capture,click=clicks.append,wait=lambda _:None,
                    input_ready=lambda frame:frame is None or frame is ingame)
            self.assertTrue(issued)
            self.assertEqual(clicks,[(480,270)])
            self.assertEqual(len(captures),2)

    def test_unknown_or_unobstructed_frame_never_clicks(self):
        for frame in (None,np.zeros((540,960),np.uint8),np.zeros((540,960,3),np.uint8)):
            clicks=[]
            with patch.object(observation,'held_placement_visible',return_value=False), \
                 patch.object(observation,'resolve_hud_panels',return_value=(False,False)):
                self.assertFalse(self.recover(capture=lambda:frame,click=clicks.append,
                    wait=lambda _:None,input_ready=lambda _:True))
            self.assertEqual(clicks,[])

    def test_actual_input_guard_preserves_pending_work_and_screen_ownership(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        function=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef)
                      and node.name=='finishedHudInputReady')
        frame=object(); state={'paused':False,'foreground':True,'screen':'INGAME'}
        env=dict(mapConfig={'steps':[]},lastIterationAction=None,skippingIteration=False,
                 routeActionExecuted=False,playToggleIssued=False,resumeProbeRan=False,
                 os=SimpleNamespace(path=SimpleNamespace(exists=lambda _:state['paused'])),PAUSE_FILE='unused',
                 windowed_input=SimpleNamespace(is_game_foreground=lambda:state['foreground']),
                 recognizeScreen=lambda *args:state['screen'],comparisonImages={},Screen=SimpleNamespace(INGAME='INGAME'))
        exec(compile(ast.Module(body=[function],type_ignores=[]),'<actual-input-owner>','exec'),env)
        ready=env['finishedHudInputReady']
        self.assertTrue(ready(frame))
        for key,value in [('lastIterationAction',{'action':'place'}),('routeActionExecuted',True),
                          ('skippingIteration',True),('playToggleIssued',True),('resumeProbeRan',True),
                          ('mapConfig',{'steps':[{'action':'ability','abilityInputSent':True}]}),
                          ('mapConfig',{'steps':[{'action':'place'}]})]:
            original=env[key];env[key]=value
            self.assertFalse(ready(frame),key);env[key]=original
        for key,value in [('paused',True),('foreground',False),('screen','VICTORY')]:
            original=state[key];state[key]=value
            self.assertFalse(ready(frame),key);state[key]=original
        self.assertTrue(ready(None))

    def test_only_finished_actions_extend_the_existing_recovery_gate(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        expression=next(node.value for node in ast.walk(tree) if isinstance(node,ast.Assign)
            and any(isinstance(target,ast.Name) and target.id=='finishedRouteHudMissing' for target in node.targets))
        for steps,money,round_number,expected in [([],90000,-1,True),([],-1,50,True),([],500,40,False),
                                                  ([{'action':'ability'}],500,-1,False),
                                                  ([{'action':'place'}],-1,-1,False)]:
            result=eval(compile(ast.Expression(expression),'<finished-only>','eval'),
                {'mapConfig':{'steps':steps},'currentValues':{'money':money,'round':round_number}})
            self.assertEqual(result,expected)

    def test_leftover_ghost_is_cancelled_without_a_world_click(self):
        for width in (960,1920,2560):
            frame=np.zeros((width*9//16,width,3),np.uint8);clicks=[]
            with patch.object(observation,'held_placement_visible',return_value=True):
                self.assertTrue(self.recover(capture=lambda:frame,click=clicks.append,
                    wait=lambda _:None,input_ready=lambda _:True))
            self.assertEqual(clicks,[(round(width*800/960),round(frame.shape[0]*60/540))])

if __name__=='__main__': unittest.main()
