"""Viewer requests must never make replay depend on untrusted file shapes."""
import ast
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest


class ViewerRequest(unittest.TestCase):
    def publisher(self, request, foreground=True):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'publishViewerFrame')
        published, inspected = [], []
        def read_or_write(name, mode='r', **kwargs):
            if name == 'viewer-request.json':
                return io.StringIO(request)
            self.assertEqual((name, mode), ('live-frame.jpg.tmp', 'wb'))
            return io.BytesIO()
        def resize(frame, size, **kwargs):
            inspected.append(frame)
            return frame
        namespace = dict(
            time=SimpleNamespace(time=lambda: 100), json=json, open=read_or_write,
            os=SimpleNamespace(replace=lambda src, dst: published.append((src, dst))),
            windowed_input=SimpleNamespace(is_game_foreground=lambda: foreground),
            cv2=SimpleNamespace(INTER_AREA=1, IMWRITE_JPEG_QUALITY=1, resize=resize,
                                imencode=lambda *args: (True, SimpleNamespace(tobytes=lambda: b'fixture'))),
            _viewerLastFrame=0,
        )
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<publishViewerFrame>', 'exec'), namespace)
        namespace['publishViewerFrame'](object())
        return published, inspected

    def test_malformed_requests_are_ignored_before_frame_work(self):
        values = [None, [], 'request', 123, {}, {'expiresAt': None},
                  {'expiresAt': 'later'}, {'expiresAt': []}, {'expiresAt': {}},
                  {'expiresAt': True}, {'expiresAt': float('nan')},
                  {'expiresAt': float('inf')}, {'expiresAt': float('-inf')}]
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(self.publisher(json.dumps(value)), ([], []))
        self.assertEqual(self.publisher('{unfinished'), ([], []))
        self.assertEqual(self.publisher('[' * 10000 + '0' + ']' * 10000), ([], []))

    def test_valid_unexpired_request_publishes(self):
        for expiry in (100001, 101000.0):
            published, inspected = self.publisher(json.dumps({'expiresAt': expiry}))
            self.assertEqual(published, [('live-frame.jpg.tmp', 'live-frame.jpg')])
            self.assertEqual(len(inspected), 1)

    def test_expired_request_does_not_publish(self):
        self.assertEqual(self.publisher('{"expiresAt":99000}'), ([], []))

    def test_unfocused_game_does_not_process_frame(self):
        self.assertEqual(self.publisher('{"expiresAt":101000}', foreground=False), ([], []))


if __name__ == '__main__':
    unittest.main()
