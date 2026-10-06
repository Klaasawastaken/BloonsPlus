using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Diagnostics;
using System.Text;
using System.Security.Cryptography;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

// Private loopback transport. No dashboard, login capture, process takeover or
// replay input belongs here; the existing controller owns environment work.
internal sealed class SetupControllerClient : IDisposable
{
    private readonly string installRoot, dataRoot, sessionId, appRoot, expectedExecutable, owner, key;
    private int port;
    private readonly string controllerReceipt;
    private readonly Action<int> launcher;
    private readonly bool savedController;
    private readonly JavaScriptSerializer serializer = new JavaScriptSerializer { MaxJsonLength = 65536 };
    private bool connected;
    private bool setupOnly;
    public SetupControllerClient(string installRoot, string dataRoot, string sessionId, int port = 4173, string expectedExecutable = null, Action<int> launcher = null) {
        Guid parsed;
        if (!Guid.TryParseExact(sessionId, "N", out parsed)) throw new ArgumentException("Invalid setup session identifier.");
        if (port < 1 || port > 65535) throw new ArgumentException("Invalid setup controller port.");
        this.installRoot = Path.GetFullPath(installRoot); this.dataRoot = Path.GetFullPath(dataRoot);
        this.sessionId = parsed.ToString("N"); this.port = port;
        appRoot = Path.Combine(this.installRoot, "resources", "app");
        this.expectedExecutable = Path.GetFullPath(expectedExecutable ?? Path.Combine(this.installRoot, "Bloons+.exe"));
        owner = Owner(appRoot);
        this.launcher = launcher;
        controllerReceipt = Path.Combine(this.dataRoot, "setup-handoff", owner + ".controller.json");
        // A receipt is a discovery hint only. Process, executable, owner and port
        // are still verified before sending a handoff or an authenticated command.
        try {
            var info = new FileInfo(controllerReceipt);
            if (info.Exists && info.Length <= 8192) {
                var receipt = serializer.Deserialize<Dictionary<string, object>>(File.ReadAllText(controllerReceipt));
                object savedOwner, executable, savedPort;
                if (receipt.TryGetValue("owner", out savedOwner) && savedOwner as string == owner
                    && receipt.TryGetValue("executable", out executable) && String.Equals(executable as string, this.expectedExecutable, StringComparison.OrdinalIgnoreCase)
                    && receipt.TryGetValue("port", out savedPort) && savedPort is int && (int)savedPort > 0 && (int)savedPort <= 65535) {
                    this.port = (int)savedPort; savedController = true;
                }
            }
        } catch { /* Invalid discovery hints never establish trust. */ }
        byte[] secret = new byte[32]; using (var random = RandomNumberGenerator.Create()) random.GetBytes(secret);
        key = BitConverter.ToString(secret).Replace("-", "").ToLowerInvariant();
    }
    internal static string Owner(string root) {
        using (var hash = SHA256.Create())
            return BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(Path.GetFullPath(root).TrimEnd('\\', '/').ToLowerInvariant())))
                .Replace("-", "").ToLowerInvariant();
    }
    private Dictionary<string, object> Request(string route, object body, bool authenticated, CancellationToken cancellation) {
        cancellation.ThrowIfCancellationRequested();
        var request = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:" + port + route);
        request.Proxy = null; request.AllowAutoRedirect = false;
        request.Timeout = request.ReadWriteTimeout = 20000;
        request.Method = body == null ? "GET" : "POST";
        if (authenticated) request.Headers["X-Bloons-Setup-Key"] = key;
        using (cancellation.Register(request.Abort)) {
            if (body != null) {
                byte[] bytes = Encoding.UTF8.GetBytes(serializer.Serialize(body));
                request.ContentType = "application/json"; request.ContentLength = bytes.Length;
                using (var stream = request.GetRequestStream()) stream.Write(bytes, 0, bytes.Length);
            }
            using (var response = (HttpWebResponse)request.GetResponse())
            using (var reader = new StreamReader(response.GetResponseStream())) {
                var text = new StringBuilder(); char[] buffer = new char[2048]; int count;
                while ((count = reader.Read(buffer, 0, buffer.Length)) > 0) {
                    text.Append(buffer, 0, count);
                    if (text.Length > 65536) throw new InvalidDataException("Setup controller response is too large.");
                }
                try {
                    var result = serializer.Deserialize<Dictionary<string, object>>(text.ToString());
                    if (result == null) throw new InvalidDataException("Setup controller returned an empty response.");
                    return result;
                } catch (ArgumentException) { throw new InvalidDataException("Setup controller response is invalid."); }
            }
        }
    }
    private void VerifyIdentity(Dictionary<string, object> identity) {
        object version, observedOwner, pid;
        if (!identity.TryGetValue("protocolVersion", out version) || !(version is int) || (int)version != 1
            || !identity.TryGetValue("owner", out observedOwner) || !String.Equals(observedOwner as string, owner, StringComparison.Ordinal)
            || !identity.TryGetValue("pid", out pid) || !(pid is int) || (int)pid <= 0)
            throw new InvalidDataException("An incompatible or unrelated controller owns this port. Close it before continuing setup.");
        try {
            if (!PortOwnedBy(port, (int)pid)) throw new InvalidDataException("Reported controller process does not own the listening port.");
            using (var process = Process.GetProcessById((int)pid)) {
                if (!String.Equals(Path.GetFullPath(process.MainModule.FileName), expectedExecutable, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("Setup controller executable does not belong to this installation.");
            }
        } catch (InvalidDataException) { throw; }
        catch { throw new InvalidDataException("Setup controller process ownership could not be confirmed."); }
    }
    [DllImport("iphlpapi.dll", SetLastError = true)]
    private static extern uint GetExtendedTcpTable(IntPtr table, ref int size, bool sorted, int family, int tableClass, uint reserved);
    internal static bool PortOwnedBy(int port, int pid) {
        IntPtr table = IntPtr.Zero;
        try {
            int size = 0;
            if (GetExtendedTcpTable(IntPtr.Zero, ref size, false, 2, 3, 0) != 122 || size < 4 || size > 1024 * 1024) return false;
            table = Marshal.AllocHGlobal(size);
            if (GetExtendedTcpTable(table, ref size, false, 2, 3, 0) != 0) return false;
            int count = Marshal.ReadInt32(table);
            if (count < 0 || count > (size - 4) / 24) return false;
            for (int row = 0; row < count; row++) {
                int offset = 4 + row * 24;
                int address = Marshal.ReadInt32(table, offset + 4);
                int encodedPort = Marshal.ReadInt32(table, offset + 8);
                int localPort = ((encodedPort & 0xff) << 8) | ((encodedPort >> 8) & 0xff);
                int ownerPid = Marshal.ReadInt32(table, offset + 20);
                if (address == 0x0100007f && localPort == port && ownerPid == pid) return true;
            }
        } catch { /* Unavailable process ownership is not permission to reuse it. */ }
        finally { if (table != IntPtr.Zero) Marshal.FreeHGlobal(table); }
        return false;
    }
    private bool PortIsFree() {
        var probe = new TcpListener(IPAddress.Loopback, port);
        try { probe.Start(); return true; }
        catch (SocketException) { return false; }
        finally { probe.Stop(); }
    }
    private Dictionary<string, object> VerifySnapshot(Dictionary<string, object> snapshot) {
        object version, identity, sequence, phase;
        if (!snapshot.TryGetValue("protocolVersion", out version) || !(version is int) || (int)version != 1
            || !snapshot.TryGetValue("sessionId", out identity) || identity as string != sessionId
            || !snapshot.TryGetValue("sequence", out sequence) || !(sequence is int || sequence is long) || Convert.ToInt64(sequence) < 0
            || !snapshot.TryGetValue("phase", out phase) || !(phase is string))
            throw new InvalidDataException("Setup response belongs to an incompatible or stale session.");
        return snapshot;
    }
    private void LaunchController() {
        if (launcher != null) { launcher(port); return; }
        if (!File.Exists(expectedExecutable) || !File.Exists(Path.Combine(appRoot, "server.js")))
            throw new FileNotFoundException("Installed setup controller is missing. Repair the local app first.");
        var start = new ProcessStartInfo(expectedExecutable, "\"" + Path.Combine(appRoot, "server.js") + "\"") {
            WorkingDirectory = appRoot, UseShellExecute = false, CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden
        };
        start.EnvironmentVariables["ELECTRON_RUN_AS_NODE"] = "1";
        start.EnvironmentVariables["BLOONS_SETUP_ONLY"] = "1";
        start.EnvironmentVariables["PORT"] = port.ToString(System.Globalization.CultureInfo.InvariantCulture);
        using (var process = Process.Start(start)) { if (process == null) throw new InvalidOperationException("Setup controller did not start."); }
    }
    private Dictionary<string, object> LaunchAndObserve(CancellationToken cancellation) {
        LaunchController();
        for (int attempt = 0; attempt < 40; attempt++) {
            cancellation.ThrowIfCancellationRequested();
            try { return Request("/api/setup/controller", null, false, cancellation); }
            catch (WebException retry) { if (retry.Status != WebExceptionStatus.ConnectFailure) throw; }
            if (cancellation.WaitHandle.WaitOne(500)) cancellation.ThrowIfCancellationRequested();
        }
        throw new InvalidOperationException("Setup controller did not become ready. Reopen setup to reconnect.");
    }
    private static int FreeLoopbackPort() {
        var probe = new TcpListener(IPAddress.Loopback, 0);
        try { probe.Start(); return ((IPEndPoint)probe.LocalEndpoint).Port; }
        finally { probe.Stop(); }
        // Another process can win the bind after this observation. VerifyIdentity
        // refuses such a process; no handoff or setup command reaches it.
    }
    public Task<Dictionary<string, object>> ConnectAsync(string operation, string isoPath, CancellationToken cancellation) {
        if (!new[] { "install", "update", "repair", "resume" }.Contains(operation)) throw new ArgumentException("Invalid setup operation.");
        return Task.Run(() => {
            Dictionary<string, object> identity = null;
            try { identity = Request("/api/setup/controller", null, false, cancellation); }
            catch (WebException error) {
                var response = error.Response as HttpWebResponse;
                if (!savedController && response != null && response.StatusCode == HttpStatusCode.NotFound) {
                    response.Dispose();
                    // An older app can own the ordinary app port. Do not stop it,
                    // send it secrets, replace it or reload its healthy replay.
                    // Start our setup-only controller on a separate free port.
                    port = FreeLoopbackPort();
                    identity = LaunchAndObserve(cancellation);
                } else {
                    // An occupied/unknown port is not permission to replace its owner.
                    if (error.Status != WebExceptionStatus.ConnectFailure || !PortIsFree()) throw;
                    identity = LaunchAndObserve(cancellation);
                }
            }
            VerifyIdentity(identity);
            object mode; setupOnly = identity.TryGetValue("setupOnly", out mode) && mode is bool && (bool)mode;
            if (setupOnly) InstallSession.AtomicWrite(controllerReceipt, serializer.Serialize(new { owner, executable = expectedExecutable, port }));
            string handoff = Path.Combine(dataRoot, "setup-handoff", sessionId + ".json");
            InstallSession.AtomicWrite(handoff, serializer.Serialize(new {
                protocolVersion = 1, sessionId, owner, operation, key,
                createdAt = (long)(DateTime.UtcNow - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalMilliseconds,
                options = new { isoPath = isoPath ?? "" }
            }));
            var result = VerifySnapshot(Request("/api/setup/session/connect", new { handoffId = sessionId }, true, cancellation));
            connected = true; return result;
        }, cancellation);
    }
    public Task<Dictionary<string, object>> ObserveAsync(CancellationToken cancellation) {
        if (!connected) throw new InvalidOperationException("Connect setup before observing it.");
        return Task.Run(() => VerifySnapshot(Request("/api/setup/session", null, true, cancellation)), cancellation);
    }
    public Task<Dictionary<string, object>> CommandAsync(long sequence, string action, CancellationToken cancellation) {
        if (!connected) throw new InvalidOperationException("Connect setup before submitting commands.");
        return Task.Run(() => VerifySnapshot(Request("/api/setup/session/command", new { sessionId, sequence, action }, true, cancellation)), cancellation);
    }
    public async Task<Dictionary<string, object>> CommandFreshAsync(string action, CancellationToken cancellation) {
        for (int attempt = 0; attempt < 3; attempt++) {
            var snapshot = await ObserveAsync(cancellation);
            try { return await CommandAsync(Convert.ToInt64(snapshot["sequence"]), action, cancellation); }
            catch (WebException error) {
                var response = error.Response as HttpWebResponse;
                if (response == null || response.StatusCode != HttpStatusCode.Conflict || attempt == 2) throw;
                response.Dispose(); // Only an explicit rejected command is safe to retry.
            }
        }
        throw new InvalidOperationException("Setup changed repeatedly. Reconnect before retrying this action.");
    }
    public Task ReleaseAsync(CancellationToken cancellation) {
        if (!connected) throw new InvalidOperationException("Connect setup before releasing it.");
        return Task.Run(() => { if (setupOnly) Request("/api/setup/session/release", new {}, true, cancellation); }, cancellation);
    }
    public void Dispose() { /* Observation ends; the controller and any owned setup work remain alive. */ }
}

internal sealed class SetupEnvironmentResult {
    public bool Ready { get; set; }
    public string HumanAction { get; set; }
    public string Status { get; set; }
    public bool RestartRequired { get; set; }
    public bool Failed { get; set; }
    public string Error { get; set; }
    public string Step { get; set; }
    internal static string SnapshotError(Dictionary<string, object> snapshot) {
        object value, message, component;
        if (!snapshot.TryGetValue("error", out value) || value == null) return null;
        var structured = value as Dictionary<string, object>;
        string text = value as string;
        if (structured != null && structured.TryGetValue("message", out message)) {
            text = message as string;
            if (!String.IsNullOrWhiteSpace(text) && structured.TryGetValue("component", out component) && component is string)
                text = (string)component + ": " + text;
        }
        return String.IsNullOrWhiteSpace(text) ? null : text.Substring(0, Math.Min(text.Length, 4096));
    }
    internal static SetupEnvironmentResult FromSnapshot(Dictionary<string, object> snapshot) {
        object value;
        string phase = snapshot.TryGetValue("phase", out value) ? value as string : null;
        bool validated = snapshot.TryGetValue("environmentValidated", out value) && value is bool && (bool)value;
        return new SetupEnvironmentResult {
            Ready = phase == "complete" && validated,
            Status = snapshot.TryGetValue("status", out value) ? value as string : "Setup status is unavailable",
            HumanAction = snapshot.TryGetValue("humanAction", out value) ? value as string : null,
            RestartRequired = phase == "restart_required",
            Failed = phase == "failed", Error = SnapshotError(snapshot),
            Step = snapshot.TryGetValue("step", out value) ? value as string : "environment"
        };
    }
}
