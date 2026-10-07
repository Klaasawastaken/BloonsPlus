import io, json, sys, tempfile, textwrap, unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'autobtd6'))
from hero_picker_memory import read_memory, lookup_hint, save_selection
class HeroHints(unittest.TestCase):
    def test_title_preprocessing_candidates_still_require_selection(self):
        source=(ROOT/'autobtd6/replay.py').read_text()
        env={};exec(source[source.index('def heroAlreadySelected('):source.index('\ndef findHeroCard(')],env)
        match=env['heroAlreadySelected']
        self.assertTrue(match('obyn_greenfoot',dict(title='noise',titleCandidates=['obyngreenfoot'],button='selected')))
        self.assertFalse(match('obyn_greenfoot',dict(title='noise',titleCandidates=['obyngreenfoot'],button='select')))
        self.assertFalse(match('obyn_greenfoot',dict(title='corvus',titleCandidates=[None,3,{},'corvus'],button='selected')))
        self.assertFalse(match('obyn_greenfoot',dict(title='',titleCandidates='obyngreenfoot',button='selected')))
        self.assertTrue(match('sauda',dict(title='auda',button='selected')))
    def test_corrupt_or_wrong_shape_cache_is_advisory(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'last-hero.json'
            for raw in ['[]','null','"psi"','not json']:
                path.write_text(raw);self.assertEqual(read_memory(path),{})
            self.assertEqual(read_memory(Path(folder)/'missing'),{})
    def test_selection_preserves_hints_and_requires_matching_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'last-hero.json';slots=[(100,100),(200,100)]
            hint=dict(page=1,position=[200,100],resolution=[1920,1080],slots=[list(p) for p in slots])
            save_selection(path,'psi',10,hint);save_selection(path,'sauda',11)
            memory=read_memory(path);self.assertEqual(memory['hero'],'sauda')
            self.assertEqual(lookup_hint(memory,'psi',(1920,1080),slots),hint)
            self.assertIsNone(lookup_hint(memory,'psi',(2560,1440),slots))
            self.assertIsNone(lookup_hint(memory,'psi',(1920,1080),[(100,100)]))
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])
    def test_invalid_hints_are_not_saved(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'last-hero.json'
            base=dict(page=0,position=[100,100],resolution=[1920,1080],slots=[[100,100]])
            for field,value in [('page',True),('page',5),('position',[101,100]),('slots',[True]),('resolution',[0,1080])]:
                save_selection(path,'psi',10,{**base,field:value})
                self.assertEqual(read_memory(path)['pickerHints'],{})
    def run_search(self,hint,titles):
        source=(ROOT/'autobtd6/replay.py').read_text();start=source.index('def findHeroCard(hero):');end=source.index('\ndef resolveRouteHero',start)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'last-hero.json';slots=[(100,100),(200,100)]
            if hint:save_selection(path,'psi',1,hint)
            clicks=[];scrolls=[];observations=iter(titles)
            env=dict(pyautogui=SimpleNamespace(size=lambda:(1920,1080),moveTo=lambda *p:None,scroll=scrolls.append,click=clicks.append),
                     imageAreas={'click':{'hero_positions':{'quincy':slots[0],'psi':slots[1]}}},
                     LAST_HERO_FILE=path,sendKey=lambda _:None,time=SimpleNamespace(sleep=lambda _:None),menuChangeDelay=0,
                     heroSelectionState=lambda:dict(title=next(observations),button='select'),
                     retainHeroPickerScanObservation=lambda *a:None,heroAlreadySelected=lambda hero,state:state['title']==hero,customPrint=lambda _:None)
            exec(source[start:end],env);result=env['findHeroCard']('psi')
            return result,clicks,scrolls
    def test_hint_is_verified_live_instead_of_trusted(self):
        hint=dict(page=1,position=[200,100],resolution=[1920,1080],slots=[[100,100],[200,100]])
        result,clicks,scrolls=self.run_search(hint,['psi'])
        self.assertEqual(clicks,[(200,100)]);self.assertEqual(result['title'],'psi');self.assertEqual(scrolls,[20,-4])
        result,clicks,scrolls=self.run_search(hint,['admiral','quincy','psi'])
        self.assertEqual(clicks,[(200,100),(100,100),(200,100)])
        self.assertEqual(scrolls,[20,-4,20]);self.assertEqual(result['pickerHint']['page'],0)
    def test_no_hint_full_search_finds_new_slot(self):
        result,clicks,scrolls=self.run_search(None,['quincy','psi'])
        self.assertEqual(clicks,[(100,100),(200,100)]);self.assertEqual(result['pickerHint']['position'],[200,100])
    def test_unchanged_final_card_stops_without_trusting_it(self):
        result,clicks,scrolls=self.run_search(None,['corvus','corvus'])
        self.assertEqual(result,{})
        self.assertEqual(clicks,[(100,100),(200,100)])
        self.assertEqual(scrolls,[20])
if __name__=='__main__':unittest.main()
