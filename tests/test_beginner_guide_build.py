import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('beginner_generator', ROOT / 'tools/generate-beginner-hard-routes.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class BeginnerGuideBuildTests(unittest.TestCase):
    def assert_build(self, text):
        tiers = {}
        for line in text.splitlines():
            words = line.split()
            if words and words[0] == 'place':
                tiers[words[2]] = [0, 0, 0]
            elif words and words[0] == 'upgrade':
                tiers[words[1]][int(words[3])] += 1
        self.assertEqual(tiers['wizard0'], [0, 2, 4])
        self.assertEqual(tiers['sniper0'], [0, 2, 4])
        self.assertEqual(tiers['dart0'], [0, 2, 4])
        self.assertEqual(tiers['druid0'], [2, 4, 0])

    def test_generator_matches_documented_build(self):
        points = [(100 + i * 100, 200, 'dart', 'point') for i in range(5)]
        self.assert_build(generator.build_route(*points))

    def test_land_build_never_falls_back_to_water_points(self):
        points = [(100, 100, 'sauda', 'hero'), (200, 200, 'sniper', 's'),
                  (300, 300, 'wizard', 'w'), (400, 400, 'buccaneer', 'b'),
                  (500, 500, 'druid', 'd'), (600, 600, 'dart', 'a')]
        chosen = generator.choose_points(points)
        self.assertTrue(all(point[2] != 'buccaneer' for point in chosen))
        with self.assertRaises(ValueError):
            generator.choose_points(points[:-1])

    def test_shipped_guide_routes_match_documented_build(self):
        routes = list((ROOT / 'autobtd6/playthroughs').glob('*#hard#1920x1080#guide#beginner-hard.btd6'))
        self.assertTrue(routes)
        for route in routes:
            with self.subTest(route=route.name):
                self.assert_build(route.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
