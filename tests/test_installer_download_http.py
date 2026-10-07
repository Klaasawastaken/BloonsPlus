"""Run the native runtime-copy boundary against real, isolated HTTP responses."""
import http.server
import os
import socket
import subprocess
import tempfile
import threading
import unittest

from native_installer_harness import compile_harness


BODY = b'MZ' + bytes(i % 251 for i in range(64 * 1024))


class DownloadHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == '/missing':
            self.send_error(404)
            return
        self.send_response(200)
        if self.path == '/chunked':
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()
            for chunk in (BODY[:1], BODY[1:1024], BODY[1024:]):
                self.wfile.write(('%x\r\n' % len(chunk)).encode() + chunk + b'\r\n')
            self.wfile.write(b'0\r\n\r\n')
            return
        payload = b'<html>Download unavailable</html>' if self.path == '/html' else BODY
        advertised = 128 * 1024 * 1024 + 1 if self.path == '/oversized' else len(payload)
        self.send_header('Content-Length', str(advertised))
        self.end_headers()
        if self.path == '/truncated':
            self.wfile.write(payload[:1024])
            self.wfile.flush()
            self.connection.shutdown(socket.SHUT_WR)
            self.close_connection = True
        else:
            self.wfile.write(payload)


@unittest.skipUnless(os.name == 'nt', 'Windows .NET Framework native boundary')
class InstallerHttpDownloadTests(unittest.TestCase):
    def test_real_http_rejects_errors_and_partial_runtime(self):
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), DownloadHandler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with tempfile.TemporaryDirectory(prefix='bloons-runtime-http-') as folder:
                binary = compile_harness(folder, 'RuntimeHttpChecks', SOURCE)
                result = subprocess.run([str(binary), 'http://127.0.0.1:%d' % server.server_port],
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('Native real HTTP runtime checks passed', result.stdout)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive(), 'Fixture HTTP server did not stop')


SOURCE = r'''
using System;
using System.IO;
using System.Net;
internal static class RuntimeHttpChecks {
    static long LastBytesWritten;
    static int LastReadCalls;
    sealed class ObservedStream : Stream {
        readonly Stream inner;
        public ObservedStream(Stream value) { inner = value; }
        public override int Read(byte[] buffer, int offset, int count) { LastReadCalls++; return inner.Read(buffer, offset, count); }
        public override bool CanRead { get { return true; } }
        public override bool CanWrite { get { return false; } }
        public override bool CanSeek { get { return false; } }
        public override long Length { get { throw new NotSupportedException(); } }
        public override long Position { get { throw new NotSupportedException(); } set { throw new NotSupportedException(); } }
        public override void Flush() { throw new NotSupportedException(); }
        public override long Seek(long offset, SeekOrigin origin) { throw new NotSupportedException(); }
        public override void SetLength(long value) { throw new NotSupportedException(); }
        public override void Write(byte[] bytes, int offset, int count) { throw new NotSupportedException(); }
    }
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static byte[] Fetch(string url, bool cancel, out long total) {
        LastBytesWritten = 0; LastReadCalls = 0;
        var request = (HttpWebRequest)WebRequest.Create(url);
        request.Proxy = null;
        request.Timeout = 3000;
        request.ReadWriteTimeout = 3000;
        long observedTotal = -2;
        using (var response = (HttpWebResponse)request.GetResponse())
        using (var source = response.GetResponseStream())
        using (var target = new MemoryStream()) {
            try {
                WindowsInstallerOperations.CopyRuntimeDownload(new ObservedStream(source), target, response.ContentLength,
                    (received, expected) => { observedTotal = expected; if (cancel) throw new OperationCanceledException(); });
            } finally { LastBytesWritten = target.Length; }
            total = observedTotal;
            return target.ToArray();
        }
    }
    static void Main(string[] args) {
        try { Run(args[0]); }
        catch (Exception error) { Console.Error.WriteLine(error.ToString()); Environment.ExitCode = 1; }
    }
    static void Run(string origin) {
        foreach (string route in new [] {"/ok", "/chunked"}) {
            long total; var bytes = Fetch(origin + route, false, out total);
            Check(bytes.Length == 65538 && bytes[0] == 77 && bytes[1] == 90, "Runtime bytes/header differ");
            for (int i=2; i<bytes.Length; i++) Check(bytes[i] == (i-2)%251, "Runtime byte mismatch");
            Check(total == (route == "/chunked" ? -1 : bytes.Length), "Known/unknown progress total differs");
        }
        foreach (string route in new [] {"/html", "/oversized", "/truncated"}) {
            bool rejected = false; long total;
            try { Fetch(origin + route, false, out total); }
            catch (InvalidDataException) { rejected = true; }
            catch (WebException error) {
                if (route != "/truncated" || error.Status == WebExceptionStatus.Timeout) throw;
                rejected = true;
            }
            Check(rejected, route + " was accepted as a complete runtime");
            if (route == "/oversized") Check(LastReadCalls == 0 && LastBytesWritten == 0, "Oversized runtime was read before rejection");
        }
        bool missing = false; long ignored;
        try { Fetch(origin + "/missing", false, out ignored); }
        catch (WebException error) {
            using (var response = error.Response as HttpWebResponse)
                missing = response != null && response.StatusCode == HttpStatusCode.NotFound;
        }
        Check(missing, "HTTP 404 was not retained as a protocol error");
        bool cancelled = false;
        try { Fetch(origin + "/ok", true, out ignored); }
        catch (OperationCanceledException) { cancelled = true; }
        Check(cancelled, "Copy ignored the cancellation callback");
        Check(LastReadCalls == 1 && LastBytesWritten > 0 && LastBytesWritten < 65538, "Cancellation waited until the complete runtime was copied");
        Console.WriteLine("Native real HTTP runtime checks passed; no installer executed.");
    }
}
'''


if __name__ == '__main__':
    unittest.main()
