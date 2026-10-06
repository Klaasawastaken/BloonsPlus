import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('round_control_audit', ROOT / 'tools/audit-round-controls.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ControlAuditTests(unittest.TestCase):
    def test_comments_case_and_lines(self):
        rows = module.controls('# start round\n  START ROUND slow # note\nchange speed\nround 10\ntoggle autostart')
        self.assertEqual([row['line'] for row in rows], [2, 3, 5])
        self.assertEqual([row['kind'] for row in rows], ['round-start', 'speed-toggle', 'autostart-toggle'])
        self.assertEqual(rows[0]['sourceBehavior'], 'One Space press.')

    def test_exact_upstream_first_argument_semantics(self):
        for command in ['start round', 'start round fast', 'start round slow extra']:
            self.assertIn('then Space again', module.controls(command)[0]['sourceBehavior'])
        for command in ['start round slow', 'start round (slow)', 'start round slow, ignored']:
            self.assertEqual(module.controls(command)[0]['sourceBehavior'], 'One Space press.')

    def test_other_commands_are_not_controls(self):
        self.assertEqual(module.controls('repeat ability 1\nwait 2\nplace dart, (0.1, 0.2), dart0'), [])


if __name__ == '__main__':
    unittest.main()
