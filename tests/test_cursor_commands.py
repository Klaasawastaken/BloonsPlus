import ast, io, re, sys, textwrap, unittest, importlib.util, tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import redirect_stdout
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'autobtd6'))
from game_runtime import normalize_action, GameState
spec=importlib.util.spec_from_file_location('cursor_import',ROOT/'tools/import-public-routes.py')
converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)
class CursorCommands(unittest.TestCase):
    def test_source_coordinates_and_rejected_arguments(self):
        for command in ['move_cursor(0.5,0.25)','move_cursor(x=0.5,y=0.25)']:
            route=converter.Route('test','test','logs','hard')
            converter.btd6bot_statement(route,ast.parse(command).body[0])
            self.assertEqual(route.lines,['move cursor to 960, 270'])
            self.assertFalse(route.lossy)
        for command in ['move_cursor(1,0.5)','move_cursor(True,0.5)','move_cursor(-0.1,0.2)','move_cursor(0.5)','move_cursor(0.5,0.5,x=0.5)']:
            with self.assertRaises(converter.Unsupported):
                converter.btd6bot_statement(converter.Route('test','test','logs','hard'),ast.parse(command).body[0])
    def test_parser_recorder_and_position_contract(self):
        source=(ROOT/'autobtd6/helper.py').read_text()
        start=source.index('    for line in configLines:');end=source.index("        if line == 'change speed':",start)
        ctx=dict(re=re,configLines=['move cursor to 960, 270'],newMapConfig={'steps':[]})
        exec('if True:\n'+source[start:end],ctx)
        action=normalize_action(ctx['newMapConfig']['steps'][0]);self.assertEqual(action['pos'],(960,270))
        start=source.index('        elif action["action"] == "move_cursor":');end=source.index('        elif action["action"] == "click":',start)
        output=io.StringIO();exec(textwrap.dedent(source[start:end]).replace('elif ','if ',1),dict(action=action,fp=output,tupleToStr=lambda p:f'{p[0]}, {p[1]}'))
        self.assertEqual(output.getvalue(),'move cursor to 960, 270\n')
        for point in [[True,2],[float('nan'),2],[1],None]:
            with self.assertRaises(ValueError):normalize_action(dict(action='move_cursor',pos=point))
    def test_replay_moves_only_and_ledger_does_not_claim_confirmation(self):
        source=(ROOT/'autobtd6/replay.py').read_text();start=source.index("                    elif action['action'] == 'move_cursor':");end=source.index("                    elif action['action'] == 'click':",start)
        moved=[];action=dict(action='move_cursor',pos=(960,270))
        exec(textwrap.dedent(source[start:end]).replace('elif ','if ',1),dict(action=action,customPrint=lambda _:None,currentValues={'round':40},pyautogui=SimpleNamespace(moveTo=moved.append)))
        self.assertEqual(moved,[(960,270)])
        state=GameState({},'offline');state.record_issued_action(action)
        self.assertEqual(state.events[-1]['status'],'issued-unverified')
        self.assertEqual(state.events[-1]['position'],[960,270])
    def test_selective_emitter_preserves_existing_routes(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder);original=output/'original.btd6';original.write_text('original')
            with patch.object(converter,'PT',output),patch.object(converter,'validate',return_value={}),redirect_stdout(io.StringIO()):
                converter.emit_cursor_candidates();before={p.name:p.read_bytes() for p in output.glob('*.btd6')}
                self.assertEqual(len(before),2)
                converter.emit_cursor_candidates();self.assertEqual(before,{p.name:p.read_bytes() for p in output.glob('*.btd6')})
                candidate=next(output.glob('*#cursor-preserved.btd6'));candidate.write_text('user edit')
                with self.assertRaisesRegex(RuntimeError,'Refusing to overwrite'):converter.emit_cursor_candidates()
            self.assertEqual(original.read_text(),'original')
if __name__=='__main__':unittest.main()
