"""Checkpoint map identity must come from an evidenced playfield, not an intro overlay."""
import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

class CheckpointScene(unittest.TestCase):
    def functions(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        names={'mapSceneSignature','sceneMatches','refreshConfirmedMapScene'}
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        env=dict(deepcopy=deepcopy)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-scene>','exec'),env)
        self.assertTrue(callable(env.get('refreshConfirmedMapScene')),'Missing evidence-based scene capture')
        return env

    def checkpoint(self):
        return dict(mapScene=[[210,150,100]]*216,mapSceneConfirmed=False,
                    map='bloody_puddles',gamemode='impoppable',runId='fixture')

    def state(self,**changes):
        return SimpleNamespace(**dict(dict(map='bloody_puddles',mode='impoppable',run_id='fixture',
                                         towers={'dart0':{'type':'dart'}}),**changes))

    def test_captures_only_once_from_matching_confirmed_placement_ledger(self):
        env=self.functions();c=self.checkpoint();frame=np.full((108,192,3),(40,30,60),dtype=np.uint8);saves=[]
        self.assertTrue(env['refreshConfirmedMapScene'](c,frame,self.state(),lambda:saves.append(deepcopy(c)) or True))
        self.assertTrue(c['mapSceneConfirmed']);self.assertEqual(c['mapScene'],[[40,30,60]]*216)
        self.assertEqual(saves[0],c)
        self.assertFalse(env['refreshConfirmedMapScene'](c,frame*0,self.state(),self.fail))
        self.assertEqual(c['mapScene'],[[40,30,60]]*216)

    def test_does_not_overwrite_legacy_or_wrong_run_and_empty_ledgers(self):
        env=self.functions();c=self.checkpoint();frame=np.zeros((108,192,3),dtype=np.uint8)
        for state in (None,self.state(towers={}),self.state(map='logs'),self.state(mode='hard'),self.state(run_id='other')):
            self.assertFalse(env['refreshConfirmedMapScene'](c,frame,state,self.fail))
            self.assertFalse(c['mapSceneConfirmed'])
        del c['mapSceneConfirmed']
        self.assertFalse(env['refreshConfirmedMapScene'](c,frame,self.state(),self.fail))

    def test_failed_persistence_restores_provisional_fingerprint(self):
        env=self.functions();c=self.checkpoint();before=deepcopy(c);frame=np.zeros((108,192,3),dtype=np.uint8)
        self.assertFalse(env['refreshConfirmedMapScene'](c,frame,self.state(),lambda:False))
        self.assertEqual(c,before)

    def test_scene_mismatch_still_rejects_different_map(self):
        env=self.functions();a=np.full((108,192,3),(40,30,60),dtype=np.uint8)
        b=np.full((108,192,3),(150,180,40),dtype=np.uint8)
        signature=env['mapSceneSignature'](a)
        self.assertTrue(env['sceneMatches'](signature,env['mapSceneSignature'](a)))
        self.assertFalse(env['sceneMatches'](signature,env['mapSceneSignature'](b)))

    def test_actual_loop_refresh_requires_in_game_state_screen_and_foreground(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text(encoding='utf-8'))
        branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If)
                    and isinstance(n.test,ast.BoolOp) and len(n.test.values)==3
                    and ast.unparse(n.test).startswith('state == State.INGAME and screen == Screen.INGAME'))
        code=compile(ast.Module(body=[branch],type_ignores=[]),'<actual-scene-owner>','exec')
        frames=[];saves=[]
        for state,screen,foreground in (('menu','ingame',True),('ingame','menu',True),('ingame','ingame',False),('ingame','ingame',True)):
            env=self.functions();checkpoint=self.checkpoint()
            env.update(state=state,screen=screen,State=SimpleNamespace(INGAME='ingame'),Screen=SimpleNamespace(INGAME='ingame'),
                       windowed_input=SimpleNamespace(is_game_foreground=lambda:foreground),routeCheckpoint=checkpoint,
                       screenshot=np.zeros((108,192,3),dtype=np.uint8),currentGameState=self.state(),
                       writeRouteCheckpoint=lambda c:saves.append(deepcopy(c)) or True,
                       customPrint=frames.append)
            exec(code,env)
            self.assertEqual(checkpoint['mapSceneConfirmed'],state==screen=='ingame' and foreground)
        self.assertEqual(len(saves),1);self.assertEqual(len(frames),1)

if __name__=='__main__':unittest.main()
