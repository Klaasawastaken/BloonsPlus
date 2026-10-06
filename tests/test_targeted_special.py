"""Offline command preservation and simulated callback order; no game input."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest
import json
import os
import subprocess
import tempfile
from unittest.mock import patch
from contextlib import redirect_stdout
import io
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('special_import', ROOT/'tools/import-public-routes.py')
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)
sys.path.insert(0, str(ROOT/'autobtd6'))
from targeted_special import perform_targeted_special

class TargetedSpecialTests(unittest.TestCase):
    def test_source_target_and_selector_are_distinct(self):
        route = importer.Route('test', 'test', 'logs', 'hard')
        route.place('gun', 'dartling', 300, 400)
        importer.btd6bot_statement(route, ast.parse('gun.special(1, x=.6, y=.7, cpos=(.2,.3))').body[0])
        self.assertEqual(route.lines[-1], 'special dartling0 to 1152, 756 at 384, 324')
        self.assertFalse(route.lossy)

    def test_second_special_preserves_target_and_selector(self):
        route = importer.Route('test', 'test', 'logs', 'hard')
        route.place('gun', 'dartling', 300, 400)
        importer.btd6bot_statement(route, ast.parse('gun.special(2, x=.6, y=.7, cpos=(.2,.3))').body[0])
        self.assertEqual(route.lines[-1], 'special2 dartling0 to 1152, 756 at 384, 324')
        self.assertFalse(route.lossy)

    def test_second_special_without_target_and_invalid_slots(self):
        route = importer.Route('test', 'test', 'logs', 'hard')
        route.place('gun', 'dartling', 300, 400)
        importer.btd6bot_statement(route, ast.parse('gun.special(s="2")').body[0])
        self.assertEqual(route.lines[-1], 'special2 dartling0')
        for slot in ('3', 'True', '2.0'):
            with self.assertRaises(importer.Unsupported):
                importer.btd6bot_statement(route, ast.parse('gun.special('+slot+')').body[0])

    def test_firing_range_has_complete_second_special_sequence(self):
        route = importer.convert_btd6bot(importer.BTD6BOT_PLANS/'firing_rangeHardChimps.py')
        self.assertFalse(route.lossy)
        self.assertEqual(route.hero, 'rosalia')
        self.assertEqual([line for line in route.lines if line.startswith('special2')], [
            'special2 hero0 to 1151, 574', 'special2 hero0 to 823, 448'])

    def test_source_audit_counts_second_targets(self):
        spec=importlib.util.spec_from_file_location('second_special_audit',ROOT/'tools/audit-btd6bot-conversions.py')
        audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
        rows=audit.audit()['findings']
        candidates=[row for row in rows if row['file'].startswith('firing_range#chimps#')]
        self.assertTrue(candidates)
        for row in candidates:
            self.assertEqual(row.get('requiredTargetSpecialCommands'),2)
        complete=next(row for row in candidates if '#second-special-preserved' in row['file'])
        self.assertEqual(complete['targetSpecialCommands'],2)
        self.assertFalse(complete['missingTargetSpecialCommands'])

    def test_candidate_preserves_existing_recordings_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)
            original=output/'firing_range#chimps#1920x1080.btd6'
            original.write_bytes(b'original recording')
            with patch.object(importer,'PT',output), patch.object(importer,'validate',return_value={}), redirect_stdout(io.StringIO()):
                importer.emit_second_special_candidate()
                before={p.name:p.read_bytes() for p in output.iterdir()}
                importer.emit_second_special_candidate()
                self.assertEqual(before,{p.name:p.read_bytes() for p in output.iterdir()})
                candidate=next(output.glob('*#second-special-preserved.btd6'))
                self.assertEqual(candidate.read_text().count('special2 hero0'),2)
                candidate.write_bytes(b'user edit')
                with self.assertRaisesRegex(RuntimeError,'Refusing to overwrite'):
                    importer.emit_second_special_candidate()
            self.assertEqual(original.read_bytes(),b'original recording')

    def test_recorder_uses_saved_second_binding_and_keeps_slot_target(self):
        tree=ast.parse((ROOT/'autobtd6/record_playthrough.py').read_text())
        nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef)
               and node.name in ('registerSecondSpecialRecording','registerSpecialRecordings','onRecordingEvent')]
        hooks=[]; modifiers=set(); events=[]
        scans=lambda key: (key,) if type(key) is int else ({'page up':(73,), 'page down':(81,)}.get(key,(99,)))
        context=dict(keyboard=SimpleNamespace(on_press_key=lambda key,callback:hooks.append((key,callback)), key_to_scan_codes=scans,
            is_pressed=lambda name:name in modifiers), re=__import__('re'),
            keybinds={'others':{'special2':'+{PgUp}'},'recording':{'monkey_special':'page down'}},
            selectedMonkey={'name':'hero0'}, config={'steps':[]}, monkeys={}, monkeysByTypeCount={},
            pyautogui=SimpleNamespace(position=lambda:(500,600),onScreen=lambda point:True),
            ahk=SimpleNamespace(get_active_window=lambda:SimpleNamespace(title='BloonsTD6')),
            isBTD6Window=lambda title:True, tupleToStr=lambda p:f'{p[0]}, {p[1]}')
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-recorder>','exec'),context)
        context['registerSecondSpecialRecording']()
        self.assertEqual(hooks[0][0],'page up')
        hooks[0][1](SimpleNamespace(scan_code=73,is_keypad=False))
        self.assertFalse(context['config']['steps'],'Required Shift is not held')
        modifiers.update(('shift','space'))
        with redirect_stdout(io.StringIO()): hooks[0][1](SimpleNamespace(scan_code=73,is_keypad=False))
        self.assertEqual(context['config']['steps'],[dict(action='special',name='hero0',specialSlot=2,to=(500,600))])
        for key in (None,'+{scf}',44,'{Numpad0}','{Del}','{Ins}'):
            hooks.clear();context['keybinds']['others']['special2']=key
            context['registerSecondSpecialRecording']()
            self.assertEqual(len(hooks),0 if key is None else 1)
        hooks.clear();modifiers.clear();context['config']['steps'].clear()
        context['keybinds']['others']['special2']='{PgDn}'
        context['registerSpecialRecordings']()
        with redirect_stdout(io.StringIO()):
            for key, callback in hooks: callback(SimpleNamespace(scan_code=81))
        self.assertEqual(context['config']['steps'],[dict(action='special',name='hero0',specialSlot=2)],
            'Saved slot-2 PageDown suppresses the legacy slot-1 PageDown hook')
        context['config']['steps'].clear()
        with redirect_stdout(io.StringIO()):
            for key, callback in hooks: callback(SimpleNamespace(scan_code=81,is_keypad=True))
        self.assertEqual(context['config']['steps'],[], 'Unbound Numpad3 is not PageDown for either slot')
        hooks.clear();context['config']['steps'].clear()
        context['keybinds']['others']['special2']='{Numpad3}'
        context['registerSpecialRecordings']()
        with redirect_stdout(io.StringIO()):
            for key, callback in hooks: callback(SimpleNamespace(scan_code=81,is_keypad=False))
        self.assertEqual(context['config']['steps'],[dict(action='special',name='hero0')],
            'PageDown must remain slot 1 when slot 2 is Numpad3')
        context['config']['steps'].clear()
        with redirect_stdout(io.StringIO()):
            for key, callback in hooks: callback(SimpleNamespace(scan_code=81,is_keypad=True))
        self.assertEqual(context['config']['steps'],[dict(action='special',name='hero0',specialSlot=2)])

    def test_runtime_key_then_target_click(self):
        calls = []
        action = dict(action='special', key='tab', pos=(100,200), to=(600,700))
        perform_targeted_special(action, lambda key:calls.append(('key',key)),
            lambda point:calls.append(('move',point)), lambda:calls.append(('click',)),
            lambda seconds:calls.append(('wait',seconds)))
        self.assertEqual([item for item in calls if item[0]!='wait'], [('key','tab'),('move',(600,700)),('click',)])
        self.assertEqual(action['pos'], (100,200))
        self.assertEqual(action['to'], (600,700))

    def test_parser_saved_binding_scaling_recording_and_resume(self):
        script = r'''
import contextlib,io,json,sys
from pathlib import Path
import helper
from game_runtime import normalize_action
from resume_recovery import restore_action
original=helper.parseBTD6InstructionFileName
helper.parseBTD6InstructionFileName=lambda name:original(Path(name).name)
helper.applyGameHotkeys(json.dumps({'monkeys':{'TowerSpecial2':{'path':'<Keyboard>/PageUp'}}}))
with contextlib.redirect_stdout(io.StringIO()):
    cfg=helper.parseBTD6InstructionsFile(sys.argv[1],targetResolution=(2560,1440),gamemode='hard')
    helper.writeBTD6InstructionsFile(cfg,folder=sys.argv[2],resolution='2560x1440')
step=cfg['steps'][1]
restored=restore_action(normalize_action(step),dict(step,key='wrong',specialSlot=1))
print(json.dumps(dict(step=step,restored=restored,recorded=next(Path(sys.argv[2]).glob('*.btd6')).read_text())))
'''
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); route=root/'logs#hard#1920x1080.btd6'
            route.write_text('place dartling gun at 300, 400\nspecial2 gun to 600, 700 at 400, 500\n')
            result=subprocess.run([sys.executable,'-X','utf8','-c',script,str(route),str(root/'output')],
                cwd=ROOT/'autobtd6',env=dict(os.environ,AHK_PATH=str(ROOT/'.venv/Scripts/AutoHotkey.exe')),
                text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            value=json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(value['step']['action'], 'special')
        self.assertEqual(value['step']['specialSlot'], 2)
        self.assertEqual(value['step']['key'], '{PgUp}')
        self.assertEqual(value['step']['pos'], [533,667])
        self.assertEqual(value['step']['to'], [800,933])
        self.assertEqual(value['restored']['specialSlot'], 2)
        self.assertEqual(value['restored']['key'], '{PgUp}')
        self.assertIn('special2 gun to 800, 933 at 533, 667', value['recorded'])

    def test_unbound_second_special_never_invents_a_key(self):
        from test_unbound_play import binding_context
        for raw in (None, '{}', json.dumps({'monkeys':{}}), json.dumps({'monkeys':{'TowerSpecial':{'path':'<Keyboard>/PageDown'}}}),
                    json.dumps({'monkeys':{'TowerSpecial2':{'path':''}}}),
                    json.dumps({'monkeys':{'TowerSpecial2':{'path':'<Mouse>/leftButton'}}})):
            context=binding_context()
            context['keybinds']['others']['special2']='stale'
            context['applyGameHotkeys'](raw)
            self.assertIsNone(context['keybinds']['others'].get('special2'))

if __name__ == '__main__': unittest.main()
