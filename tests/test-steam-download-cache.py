import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('vm_setup', Path(__file__).resolve().parents[1] / 'vm/setup-vm.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class Response(io.BytesIO):
    def __init__(self, data, length=None):
        super().__init__(data)
        self.headers = {'Content-Length': str(len(data) if length is None else length)}


class CacheTests(unittest.TestCase):
    def test_completed_download_reused_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'SteamSetup.exe'
            with patch.object(setup.urllib.request, 'urlopen', return_value=Response(b'MZexample')) as download:
                setup.cached_steam_installer(target)
                setup.cached_steam_installer(target)
            self.assertEqual(download.call_count, 1)
            self.assertEqual(target.read_bytes(), b'MZexample')

    def test_untracked_old_partial_is_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'SteamSetup.exe'
            target.write_bytes(b'MZbroken')
            with patch.object(setup.urllib.request, 'urlopen', return_value=Response(b'MZcomplete')):
                setup.cached_steam_installer(target)
            self.assertEqual(target.read_bytes(), b'MZcomplete')

    def test_truncated_download_is_not_promoted(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'SteamSetup.exe'
            with patch.object(setup.urllib.request, 'urlopen', return_value=Response(b'MZshort', 500)):
                with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                    setup.cached_steam_installer(target)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(folder).glob('*.part')), [])

    def test_changed_cached_bytes_are_downloaded_again(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'SteamSetup.exe'
            with patch.object(setup.urllib.request, 'urlopen', return_value=Response(b'MZexample')):
                setup.cached_steam_installer(target)
            target.write_bytes(b'MZchanged')
            with patch.object(setup.urllib.request, 'urlopen', return_value=Response(b'MZrestored')) as download:
                setup.cached_steam_installer(target)
            self.assertEqual(download.call_count, 1)
            self.assertEqual(target.read_bytes(), b'MZrestored')

    def test_error_page_does_not_replace_existing_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'SteamSetup.exe'
            target.write_bytes(b'old-cache')
            with patch.object(setup.urllib.request, 'urlopen', return_value=Response(b'<html>error</html>')):
                with self.assertRaisesRegex(RuntimeError, 'executable'):
                    setup.cached_steam_installer(target)
            self.assertEqual(target.read_bytes(), b'old-cache')

    def test_network_interruption_cleans_temporary_download(self):
        class Interrupted(Response):
            def read(self, size=-1):
                if self.tell():
                    raise TimeoutError('network stalled')
                return super().read(3)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'SteamSetup.exe'
            with patch.object(setup.urllib.request, 'urlopen', return_value=Interrupted(b'MZexample')):
                with self.assertRaises(TimeoutError):
                    setup.cached_steam_installer(target)
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
