import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('brand_tokens', ROOT / 'installer/brand_tokens.py')
tokens = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tokens)


class BrandTokenTests(unittest.TestCase):
    def test_native_and_web_share_exact_generated_colors(self):
        source = json.loads((ROOT / 'data/config/brand-tokens.json').read_text())
        native, web = tokens.render(source)
        self.assertEqual(native, (ROOT / 'installer/native/BrandTokens.cs').read_text())
        self.assertEqual(web, (ROOT / 'assets/app/brand-tokens.css').read_text())
        for theme in source['colors'].values():
            for value in theme.values():
                self.assertIn(value, native)
                self.assertIn(value, web)

    def test_invalid_color_cannot_enter_generated_sources(self):
        source = {'colors': {'light': {'text':'"; arbitrary code'}}}
        with self.assertRaises(ValueError):
            tokens.render(source)
