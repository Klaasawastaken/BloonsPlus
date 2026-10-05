"""Offline conversion checks; never launches the game or rewrites recordings."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("route_import", ROOT / "tools/import-public-routes.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HeroPurchaseTests(unittest.TestCase):
    def route(self):
        route = module.Route("test", "test", "resort", "easy", "sauda")
        route.place("sauda", "hero", 800, 300)
        return route

    def test_incremental_hero_purchase_rejected(self):
        route = self.route()
        with self.assertRaisesRegex(module.Unsupported, "paid hero levels"):
            route.upgrade("sauda", 0)
        self.assertFalse(route.harmless)

    def test_absolute_hero_purchase_rejected(self):
        with self.assertRaisesRegex(module.Unsupported, "paid hero levels"):
            self.route().upgrade_to("sauda", [1, 0, 0])

    def test_bloonsplayer_purchase_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "hero.txt"
            source.write_text("open resort, easy, primary only, sauda\n"
                              "place hero, (0.79669, 0.19910), sauda\n"
                              "upgrade sauda, 4\n", encoding="utf-8")
            with self.assertRaisesRegex(module.Unsupported, "paid hero levels"):
                module.convert_bloonsplayer(source)

    def test_normal_tower_upgrade_preserved(self):
        route = self.route()
        route.place("dart", "dart", 900, 400)
        route.upgrade("dart", 0)
        self.assertEqual(route.lines[-1], "upgrade dart0 path 0")


if __name__ == "__main__":
    unittest.main()
