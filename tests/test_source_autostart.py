"""Pinned source toggles retain an explicit initial setting; no game input."""
import ast
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_autostart_import',ROOT/'tools/import-public-routes.py')
converter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class SourceAutoStart(unittest.TestCase):
    def test_source_toggle_sequence_has_one_initial_baseline(self):
        route=converter.Route('btd6bot','fixture','logs','hard')
        route.lines.append('wait 2 seconds')
        for command in ('change_autostart()',)*3:
            converter.btd6bot_statement(route,ast.parse(command).body[0])
        self.assertEqual(route.lines,['autostart on','wait 2 seconds','autostart off','autostart on','autostart off'])
        self.assertFalse(route.lossy)

    def test_invalid_arguments_leave_no_partial_toggle(self):
        for command in ('change_autostart(True)','change_autostart(enabled=False)'):
            route=converter.Route('btd6bot','fixture','logs','hard')
            with self.assertRaises(converter.Unsupported):
                converter.btd6bot_statement(route,ast.parse(command).body[0])
            self.assertEqual(route.lines,[])
            self.assertTrue(route.source_autostart)
            self.assertFalse(route.source_autostart_initialized)

    def test_pinned_sanctuary_remains_gated_on_manual_round_controls(self):
        route=converter.convert_btd6bot(ROOT/'btd6bot/btd6bot/plans/sanctuaryHardChimps.py')
        self.assertEqual(route.lines[0],'autostart on')
        self.assertIn('autostart off',route.lines)
        self.assertNotIn('change_autostart() control omitted',route.lossy)
        self.assertIn('end_round() control omitted',route.lossy)
        self.assertIn('forward() control omitted',route.lossy)

    def test_routes_without_toggles_gain_no_setting_commands(self):
        route=converter.Route('btd6bot','fixture','logs','hard')
        converter.btd6bot_statement(route,ast.parse('wait(2)').body[0])
        self.assertEqual(route.lines,['wait 2 seconds'])


if __name__=='__main__':unittest.main()
