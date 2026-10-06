"""Actual parser/writer/replay branch checks with simulated input only."""
import ast
from copy import deepcopy
import io
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'autobtd6'))
from autostart_control import drive_autostart, pending_autostart_step, parse_autostart_command, serialize_autostart_command
from autostart_observation import observe_autostart
from game_runtime import normalize_action
from purchase_pacing import pacing_allowed


def executable(nodes):
    return compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), '<actual-source>', 'exec')


class AutoStartIntegration(unittest.TestCase):
    def test_actual_parser_and_writer_round_trip(self):
        tree = ast.parse((ROOT/'autobtd6/helper.py').read_text(encoding='utf-8'))
        loop = next(node for node in ast.walk(tree) if isinstance(node, ast.For)
                    and node.body and isinstance(node.body[0], ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'autoStart' for target in node.body[0].targets))
        parser = ast.For(target=loop.target, iter=loop.iter, body=loop.body[:2], orelse=[])
        writer = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                      and isinstance(node.test, ast.Compare) and any(isinstance(n, ast.Constant) and n.value == 'set_autostart' for n in ast.walk(node.test)))
        for enabled in (False, True):
            line = 'autostart on' if enabled else 'autostart off'
            env = dict(configLines=[line], newMapConfig={'steps': []}, parse_autostart_command=parse_autostart_command)
            exec(executable([parser]), env)
            step = env['newMapConfig']['steps'][0]
            self.assertEqual(normalize_action(step)['enabled'], enabled)
            output = io.StringIO()
            exec(executable([writer]), dict(action=step, fp=output, serialize_autostart_command=serialize_autostart_command))
            self.assertEqual(output.getvalue(), line+'\n')
        with self.assertRaises(ValueError):
            exec(executable([parser]), dict(configLines=['autostart toggle'], newMapConfig={'steps': []}, parse_autostart_command=parse_autostart_command))
        for value in (0, 1, 'on', None):
            with self.assertRaises(ValueError): normalize_action(dict(action='set_autostart', enabled=value))

    def test_explicit_setting_disables_purchase_pacing(self):
        self.assertFalse(pacing_allowed([parse_autostart_command('autostart off')]))
        self.assertTrue(pacing_allowed([dict(action='place')]))

    def test_completion_save_failure_keeps_recorded_step_and_mode(self):
        step = dict(action='set_autostart', enabled=False, routeStepIndex=4,
                    autostartPending=dict(phase='closing', sentAt=10, session='process'))
        config = dict(steps=[step, dict(action='await_round', round=20, routeStepIndex=5)], autostartEnabled=True)
        calls=[]
        result = drive_autostart(config, 12, 'ingame', None, True, 'process', calls.append, calls.append, lambda:False)
        self.assertEqual(result,(True,False))
        self.assertEqual(config['steps'][0],step)
        self.assertTrue(config['autostartEnabled'])
        result = drive_autostart(config, 13, 'ingame', None, True, 'process', calls.append, calls.append)
        self.assertEqual(result,(True,False))
        self.assertFalse(config['autostartEnabled'])
        self.assertEqual(config['steps'][0]['routeStepIndex'],5)
        self.assertEqual(calls,[])

    def test_resume_check_never_changes_recorded_queue_indices(self):
        queue=[dict(action='await_round',round=20,routeStepIndex=5)]
        check=dict(action='set_autostart',enabled=False,autostartPending=dict(phase='closing',sentAt=10,session='process'))
        config=dict(steps=deepcopy(queue),resumeAutostartCheck=check)
        self.assertEqual(drive_autostart(config,12,'ingame',None,True,'process',lambda key:None,lambda point:None),(True,False))
        self.assertNotIn('resumeAutostartCheck',config)
        self.assertEqual(config['steps'],queue)
        self.assertFalse(config['autostartEnabled'])

    def test_resume_check_save_failure_remains_owned(self):
        check=dict(action='set_autostart',enabled=False,autostartPending=dict(phase='closing',sentAt=10,session='process'))
        config=dict(steps=[],resumeAutostartCheck=check)
        self.assertEqual(drive_autostart(config,12,'ingame',None,True,'process',lambda key:None,lambda point:None,lambda:False),(True,False))
        self.assertEqual(config['resumeAutostartCheck'],check)
        self.assertNotIn('autostartEnabled',config)

    def test_actual_replay_branch_owns_menu_and_preserves_purchase_confirmations(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch=next(node for node in ast.walk(tree) if isinstance(node,ast.If)
                    and node.body and isinstance(node.body[0],ast.Assign)
                    and any(isinstance(target,ast.Name) and target.id=='autoStep' for target in node.body[0].targets))
        code=executable([ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.Tuple(elts=[ast.Constant(1)],ctx=ast.Load()),body=branch.body[:4],orelse=[])])
        reference=cv2.imread(str(ROOT/'autobtd6/images/1920x1080/ingame_paused.png'))
        for previous, known_round, expected in ((None,10,['{Esc}']),
                                                 (dict(action='place'),10,[]),
                                                 (dict(action='upgrade'),10,[]),
                                                 (None,None,[]), (None,0,[]), (None,True,[])):
            sent=[]
            config=dict(steps=[dict(action='set_autostart',enabled=True,routeStepIndex=0,cost=0)])
            checkpoint=dict(round=known_round)
            env=dict(mapConfig=config,lastIterationAction=previous,routeCheckpoint=checkpoint,
                     routeStepTotal=1,screen='ingame',Screen=SimpleNamespace(INGAME='ingame',INGAME_PAUSED='pause'),
                     state='state',screenshot=reference,comparisonImages={'screens':{'ingame_paused':reference}},
                     time=SimpleNamespace(time=lambda:10,sleep=lambda seconds:None),autostartSession='process',
                     pending_autostart_step=pending_autostart_step,drive_autostart=drive_autostart,
                     observe_autostart=observe_autostart,windowed_input=SimpleNamespace(is_game_foreground=lambda:True),
                     sendKey=sent.append,pyautogui=SimpleNamespace(click=sent.append),customPrint=lambda message:None,
                     checkpointStepOffset=lambda steps,total:steps[0]['routeStepIndex'] if steps else total,
                     writeRouteCheckpoint=lambda cp,steps:True)
            exec(code,env)
            self.assertEqual(sent,expected)
            self.assertEqual(len(config['steps']),1,'opening cannot consume setting')

    def test_actual_automatic_round_control_respects_manual_setting(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        condition=next(node for node in ast.walk(tree) if isinstance(node,ast.BoolOp)
                       and any(isinstance(child,ast.Call) and isinstance(child.func,ast.Attribute)
                               and child.func.attr=='get' and any(isinstance(arg,ast.Constant) and arg.value=='autostartEnabled' for arg in child.args)
                               for child in ast.walk(node))
                       and len(node.values)==2 and isinstance(node.values[1],ast.UnaryOp))
        code=compile(ast.Expression(body=condition),'<actual-round-gate>','eval')
        for config, expected in ((dict(steps=[{}],autostartEnabled=False),False),
                                 (dict(steps=[],autostartEnabled=False),True),
                                 (dict(steps=[{}],autostartEnabled=True),True),
                                 (dict(steps=[{}]),True)):
            self.assertEqual(eval(code,dict(mapConfig=config)),expected)

    def test_actual_resume_menu_closes_only_with_evidence_and_foreground(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch=next(node for node in ast.walk(tree) if isinstance(node,ast.If)
                    and isinstance(node.test,ast.BoolOp)
                    and any(isinstance(child,ast.Name) and child.id=='resumeAutoStep'
                            for child in ast.walk(node.test)))
        frame=np.zeros((1080,1920,3),dtype=np.uint8)
        for confirmed, foreground, expected in ((False,True,[]),(True,False,[]),(True,True,['{Esc}','wait','capture','recognize'])):
            calls=[]
            def capture():
                calls.append('capture');return frame
            def recognize(image, references):
                calls.append('recognize');return 'ingame'
            env=dict(resumeAutoStep={'action':'set_autostart','enabled':False},resumeScreen='pause',
                     Screen=SimpleNamespace(INGAME_PAUSED='pause'),resumeImage=frame,
                     comparisonImages={'screens':{'ingame_paused':frame}},
                     observe_autostart=lambda *args:dict(pauseConfirmed=confirmed),
                     windowed_input=SimpleNamespace(is_game_foreground=lambda:foreground),
                     customPrint=lambda message:None,sendKey=calls.append,
                     time=SimpleNamespace(sleep=lambda seconds:calls.append('wait')),
                     pyautogui=SimpleNamespace(screenshot=capture),np=np,recognizeScreen=recognize)
            exec(executable([branch]),env)
            self.assertEqual(calls,expected)
            self.assertEqual(env['resumeScreen'],'ingame' if expected else 'pause')

    def test_actual_generic_action_gate_cannot_pop_setting_command(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        guard=next(node for node in ast.walk(tree) if isinstance(node,ast.If)
                   and isinstance(node.test,ast.Compare) and isinstance(node.test.left,ast.Name)
                   and node.test.left.id=='nextStepAction' and isinstance(node.test.comparators[0],ast.Constant)
                   and node.test.comparators[0].value=='set_autostart')
        env=dict(nextStepAction='set_autostart',nextStepDelayReady=True)
        exec(executable([guard]),env)
        self.assertFalse(env['nextStepDelayReady'])


if __name__=='__main__': unittest.main()
