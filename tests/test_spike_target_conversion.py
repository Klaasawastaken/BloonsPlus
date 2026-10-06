"""Faithful Spike Factory Smart-target conversion without game input."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io
import ast
import json
import os
import subprocess
import sys
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
        for bottom,target in [(1,'smart'),(1,'close'),(2,'unknown')]:
            route=self.route(bottom);before=list(route.lines)
            route.set_target('spike',target)
            self.assertTrue(route.lossy,(bottom,target))
            self.assertEqual(route.lines,before)

    def test_normal_close_smart_forward_sequence_with_moving_selector(self):
        route=self.route();route.update_selection('spike',(0.3,0.4));before=len(route.lines)
        route.set_target('spike','close');route.set_target('spike','close');route.set_target('spike','smart')
        self.assertFalse(route.lossy)
        self.assertEqual(route.lines[before:],['retarget spike0 at 576, 432']*2)
        route.set_target('spike','close')
        self.assertFalse(route.lossy)
        self.assertEqual(route.lines[before:],['retarget spike0 at 576, 432']*2 + ['retarget spike0 reverse at 576, 432'])

    def test_all_source_cycle_transitions_including_tier_five(self):
        cycle = ['normal', 'close', 'smart', 'set', 'automatic']
        for bottom in (2, 5):
            for current in cycle:
                for desired in cycle:
                    with self.subTest(bottom=bottom,current=current,desired=desired):
                        route=self.route(bottom);route.towers['spike0']['spikeTarget']=current
                        before=len(route.lines);route.set_target('spike',desired)
                        delta=(cycle.index(desired)-cycle.index(current)) % 5
                        reverse=delta > 2
                        self.assertFalse(route.lossy)
                        self.assertEqual(route.lines[before:],
                            ['retarget spike0' + (' reverse' if reverse else '')] * (5-delta if reverse else delta))
                        self.assertEqual(route.towers['spike0']['spikeTarget'],desired)

    def test_set_target_click_keeps_selection_coordinate_independent(self):
        route=self.route(5);before=len(route.lines)
        m.btd6bot_statement(route,ast.parse('spike.target("set", .8, .6, cpos=(.3,.4))').body[0])
        self.assertFalse(route.lossy)
        self.assertEqual(route.lines[before:],[
            'retarget spike0 reverse at 576, 432',
            'retarget spike0 reverse at 576, 432',
            'special spike0 to 1536, 648 at 576, 432'])
        for value in ('True', '-.1', '1'):
            route=self.route();before=list(route.lines)
            with self.assertRaises(m.Unsupported):
                m.btd6bot_statement(route,ast.parse('spike.target("set", '+value+', .4)').body[0])
            self.assertEqual(route.lines,before)

    def test_source_set_click_typo_is_not_silently_reinterpreted(self):
        # Pinned source concatenates "smart" and ", automatic" in its Set
        # click guard. Such calls need a source repair, not an invented input.
        for current in ('smart','automatic'):
            route=self.route();route.towers['spike0']['spikeTarget']=current
            before=list(route.lines);route.set_target('spike','set',to=(800,600))
            self.assertTrue(route.lossy)
            self.assertEqual(route.lines,before)

    def test_actual_last_resort_and_erosion_convert_without_omissions(self):
        for name in ('last_resortHardChimps.py','erosionHardChimps.py'):
            route=m.convert_btd6bot(m.BTD6BOT_PLANS/name)
            self.assertFalse(route.lossy,(name,route.lossy))
            self.assertTrue(any(' reverse' in line for line in route.lines))
        erosion=m.convert_btd6bot(m.BTD6BOT_PLANS/'erosionHardChimps.py')
        self.assertIn('special spike0 to 1523, 500',erosion.lines)

    def test_reverse_parser_binding_scaling_recording_and_resume(self):
        script=r'''
import contextlib,io,json,sys
from pathlib import Path
import helper
from game_runtime import normalize_action
from resume_recovery import restore_action
original=helper.parseBTD6InstructionFileName
helper.parseBTD6InstructionFileName=lambda name:original(Path(name).name)
helper.applyGameHotkeys(json.dumps({'monkeys':{'ReverseChangeTargeting':{'path':'<Keyboard>/tab','modifierKey':1}}}))
with contextlib.redirect_stdout(io.StringIO()):
    cfg=helper.parseBTD6InstructionsFile(sys.argv[1],targetResolution=(2560,1440),gamemode='hard')
    helper.writeBTD6InstructionsFile(cfg,folder=sys.argv[2],resolution='2560x1440')
step=cfg['steps'][1];restored=restore_action(normalize_action(step),dict(step,key='wrong'))
print(json.dumps(dict(step=step,restored=restored,recorded=next(Path(sys.argv[2]).glob('*.btd6')).read_text())))
'''
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);route=root/'logs#hard#1920x1080.btd6'
            route.write_text('place spike spike0 at 300, 400\nretarget spike0 reverse at 600, 700\n')
            result=subprocess.run([sys.executable,'-X','utf8','-c',script,str(route),str(root/'output')],
                cwd=ROOT/'autobtd6',env=dict(os.environ,AHK_PATH=str(ROOT/'.venv/Scripts/AutoHotkey.exe')),
                text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            value=json.loads(result.stdout.strip().splitlines()[-1])
        self.assertTrue(value['step']['reverse'])
        self.assertEqual(value['step']['key'],'+{scf}')
        self.assertEqual(value['step']['pos'],[800,933])
        self.assertEqual(value['restored']['key'],'+{scf}')
        self.assertTrue(value['restored']['reverse'])
        self.assertIn('retarget spike0 reverse at 800, 933',value['recorded'])

    def test_unbound_reverse_never_invents_a_key(self):
        from test_unbound_play import binding_context
        for binding in (None,{'path':''},{'path':'<Mouse>/leftButton'}):
            context=binding_context();monkeys={'ChangeTargeting':{'path':'<Keyboard>/tab'}}
            if binding is not None:monkeys['ReverseChangeTargeting']=binding
            context['applyGameHotkeys'](json.dumps({'monkeys':monkeys}))
            self.assertIsNone(context['keybinds']['others'].get('retarget_reverse'))

    def test_replay_batches_only_bound_actions_on_same_selected_tower(self):
        tree=ast.parse((ROOT/'autobtd6/replay.py').read_text())
        condition=next(node.test for node in ast.walk(tree) if isinstance(node,ast.If)
            and node.body and isinstance(node.body[0],ast.Assign)
            and any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='pop'
                    for n in ast.walk(node.body[0]))
            and 'retarget' in ast.unparse(node.test))
        current=dict(action='upgrade',name='spike0',pos=(100,200),key='comma')
        for action,key,pos,expected in [('retarget','tab',(100,200),True),
                ('retarget',None,(100,200),False),('special',None,(100,200),False),
                ('special','f1',(300,400),False),('click',None,(300,400),True)]:
            next_step=dict(action=action,name='spike0',key=key,pos=pos)
            actual=eval(compile(ast.Expression(condition),'<actual-batch-guard>','eval'),
                dict(mapConfig={'steps':[next_step]},action=current))
            self.assertEqual(actual,expected,(action,key,pos))

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

    def test_full_cycle_candidates_are_separate_and_scoped(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);plans=root/'plans';plans.mkdir();out=root/'routes';out.mkdir()
            for name in ('last_resortHardChimps.py','erosionHardChimps.py','logsHardStandard.py'):
                (plans/name).write_text('[Hero] -\n')
            original=out/'erosion#chimps#1920x1080#converted#lossy.btd6';original.write_bytes(b'original recording')
            def convert(path):
                route=self.route(5);route.map=path.name.split('Hard')[0];route.mode='chimps'
                route.set_target('spike','set',to=(800,600));return route
            with patch.object(m,'BTD6BOT_PLANS',plans),patch.object(m,'PT',out),patch.object(m,'convert_btd6bot',side_effect=convert),patch.object(m,'validate',return_value={}),redirect_stdout(io.StringIO()):
                m.emit_spike_target_candidates('cycle')
                candidates=list(out.glob('*spike-cycle-preserved.btd6'))
                self.assertEqual(len(candidates),2)
                before={path.name:path.read_bytes() for path in candidates}
                m.emit_spike_target_candidates('cycle')
                self.assertEqual({path.name:path.read_bytes() for path in candidates},before)
                self.assertEqual(original.read_bytes(),b'original recording')
                candidates[0].write_bytes(b'edited candidate')
                with self.assertRaisesRegex(RuntimeError,'Refusing to overwrite'):
                    m.emit_spike_target_candidates('cycle')

if __name__=='__main__':unittest.main()
