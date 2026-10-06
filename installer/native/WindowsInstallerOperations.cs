using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
using System.Net;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using System.Threading;

// Windows operations know paths and processes, never controls or window handles.
internal class WindowsInstallerOperations : IDisposable
{
    protected readonly InstallerOptions options;
    private string installRoot { get { return options.InstallRoot; } }
    private string logPath { get { return options.LogPath; } }
    private readonly OwnedProcess ownedProcess;
    internal CancellationToken Cancellation { get; set; }
    public event Action<InstallerProgress> ProgressChanged;
    public event Action<string> DetailAdded;
    public event Action<string> LogAdded;
    public event Action<Dictionary<string, object>> EnvironmentChanged;
    public WindowsInstallerOperations(InstallerOptions options) {
        if (options == null) throw new ArgumentNullException("options");
        this.options = options;
        ownedProcess = new OwnedProcess(options.InstallRoot);
    }
    protected void SetStatus(string text, InstallerStage stage, int? percent = null, string scope = null, long? numerator = null, long? denominator = null) {
        var state = new InstallerProgress { Message = text };
        state.Update(stage, percent, scope);
        if (numerator.HasValue && denominator.HasValue) state.Measure(numerator.Value, denominator.Value);
        var handler = ProgressChanged; if (handler != null) handler(state);
    }
    protected void SetDetail(string text) { var handler = DetailAdded; if (handler != null) handler(text); }
    protected void Log(string text) { var handler = LogAdded; if (handler != null) handler(text); }
    public void Dispose() { ownedProcess.Dispose(); }
    public virtual SetupEnvironmentResult ConfigureEnvironment(string sessionId) {
        using (var controller = new SetupControllerClient(installRoot, options.DataRoot, sessionId)) {
            var snapshot = controller.ConnectAsync("install", options.RequestedIsoPath, Cancellation).GetAwaiter().GetResult();
            string phase = snapshot.ContainsKey("phase") ? snapshot["phase"] as string : null;
            if (phase == "idle" || phase == "failed" || phase == "cancelled" || phase == "validating")
                snapshot = controller.CommandAsync(Convert.ToInt64(snapshot["sequence"]), phase == "idle" ? "start" : "resume", Cancellation).GetAwaiter().GetResult();
            DateTime deadline = DateTime.UtcNow.AddHours(2);
            while (true) {
                Cancellation.ThrowIfCancellationRequested();
                var handler = EnvironmentChanged; if (handler != null) handler(snapshot);
                var result = SetupEnvironmentResult.FromSnapshot(snapshot);
                if (result.Ready) { controller.ReleaseAsync(Cancellation).GetAwaiter().GetResult(); return result; }
                if (!String.IsNullOrEmpty(result.HumanAction) && result.HumanAction != "wait_replay") return result;
                if (DateTime.UtcNow >= deadline) return new SetupEnvironmentResult { HumanAction = "retry", Status = "Setup is still being observed. Reopen setup to reconnect; existing work remains running." };
                if (Cancellation.WaitHandle.WaitOne(1500)) {
                    // Cancel scheduling through the coordinator, never kill a shared
                    // dependency or a healthy replay to dismiss the installer.
                    try { controller.CommandAsync(Convert.ToInt64(snapshot["sequence"]), "cancel", CancellationToken.None).GetAwaiter().GetResult(); } catch { }
                    Cancellation.ThrowIfCancellationRequested();
                }
                snapshot = controller.ObserveAsync(Cancellation).GetAwaiter().GetResult();
            }
        }
    }
    public virtual void ReadEmbeddedPackage(string tempZip) {
            using (FileStream installer = new FileStream(options.InstallerPath, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                if (installer.Length < 16) throw new InvalidDataException("The installer package is incomplete.");
                installer.Seek(-16, SeekOrigin.End);
                byte[] footer = new byte[16];
                installer.Read(footer, 0, footer.Length);
                string marker = Encoding.ASCII.GetString(footer, 0, 8);
                long zipLength = BitConverter.ToInt64(footer, 8);
                long zipOffset = installer.Length - 16 - zipLength;
                if (marker != "BLPZIP01" || zipLength <= 0 || zipOffset <= 0)
                    throw new InvalidDataException("The embedded app package could not be located.");
                installer.Seek(zipOffset, SeekOrigin.Begin);
                using (FileStream zipFile = new FileStream(tempZip, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                {
                    byte[] buffer = new byte[1024 * 1024];
                    long remaining = zipLength;
                    while (remaining > 0)
                    {
                        Cancellation.ThrowIfCancellationRequested();
                        int read = installer.Read(buffer, 0, (int)Math.Min(buffer.Length, remaining));
                        if (read <= 0) throw new EndOfStreamException("The embedded app package ended early.");
                        zipFile.Write(buffer, 0, read);
                        remaining -= read;
                    }
                }
            }

    }
    public virtual void InstallAppFiles(string tempZip) {
            SetStatus("Installing Bloons+ files…", InstallerStage.Files, 0);
            using (FileStream package = new FileStream(tempZip, FileMode.Open, FileAccess.Read, FileShare.Read))
            using (ZipArchive archive = new ZipArchive(package, ZipArchiveMode.Read))
            {
                long totalBytes = Math.Max(1, archive.Entries.Sum(entry => entry.Length));
                long writtenBytes = 0;
                int reusedFiles = 0;
                byte[] buffer = new byte[1024 * 1024];
                foreach (ZipArchiveEntry entry in archive.Entries)
                {
                    Cancellation.ThrowIfCancellationRequested();
                    string destination = SafeDestination(installRoot, entry.FullName);
                    if (entry.FullName.EndsWith("/", StringComparison.Ordinal) || entry.FullName.EndsWith("\\", StringComparison.Ordinal))
                    {
                        Directory.CreateDirectory(destination);
                        continue;
                    }
                    if (SameAsArchiveEntry(entry, destination)) {
                        writtenBytes += entry.Length;
                        reusedFiles++;
                        continue;
                    }
                    Directory.CreateDirectory(Path.GetDirectoryName(destination));
                    string staged = destination + "." + Guid.NewGuid().ToString("N") + ".tmp";
                    try {
                        using (Stream input = entry.Open())
                        using (FileStream output = new FileStream(staged, FileMode.CreateNew, FileAccess.Write, FileShare.None)) {
                            int read;
                            while ((read = input.Read(buffer, 0, buffer.Length)) > 0) {
                                Cancellation.ThrowIfCancellationRequested();
                                output.Write(buffer, 0, read);
                                writtenBytes += read;
                            }
                            output.Flush(true);
                        }
                        if (!SameAsArchiveEntry(entry, staged)) throw new InvalidDataException("An app file failed verification before replacement.");
                        CommitStagedFile(staged, destination);
                    } finally {
                        if (File.Exists(staged)) File.Delete(staged);
                    }
                    if (writtenBytes % (64L * 1024 * 1024) < buffer.Length)
                        SetStatus("Installing Bloons+ files… " + (writtenBytes / (1024 * 1024)).ToString("N0") + " MB", InstallerStage.Files, (int)(writtenBytes * 100 / totalBytes), "Copy", writtenBytes, totalBytes);
                }
                SetStatus("App files ready; reused " + reusedFiles + " unchanged files.", InstallerStage.Files, 100, "Copy", writtenBytes, totalBytes);
            }

    }
    protected virtual void CommitStagedFile(string staged, string destination) {
        if (File.Exists(destination)) File.Replace(staged, destination, null);
        else File.Move(staged, destination);
    }
    public virtual void LaunchApp() {
        Process.Start(new ProcessStartInfo(Path.Combine(installRoot, "Bloons+.exe")) { WorkingDirectory = installRoot, UseShellExecute = true });
    }
    private static string SafeDestination(string root, string entryName)
    {
        string normalized = entryName.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar);
        string destination = Path.GetFullPath(Path.Combine(root, normalized));
        string prefix = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!destination.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Installer archive contains an invalid path.");
        return destination;
    }

    private static string HashFile(string file)
    {
        using (SHA256 hash = SHA256.Create())
        using (FileStream input = File.OpenRead(file))
            return BitConverter.ToString(hash.ComputeHash(input));
    }

    private static bool SameAsArchiveEntry(ZipArchiveEntry entry, string destination)
    {
        if (!File.Exists(destination) || new FileInfo(destination).Length != entry.Length) return false;
        using (SHA256 hash = SHA256.Create())
        using (Stream input = entry.Open())
            return BitConverter.ToString(hash.ComputeHash(input)) == HashFile(destination);
    }

    public virtual void BackupExistingData(string backupRoot)
    {
        string[] preserve = {
            "resources/app/automation-progress.json",
            "resources/app/game-observations.json",
            "resources/app/data/config/calibration.json",
            "resources/app/data/config/map-order.json",
            "resources/app/route-verification.json",
            "resources/app/autobtd6/userconfig.json",
            "resources/app/autobtd6/playthrough_stats.json"
        };
        foreach (string relative in preserve)
        {
            string source = SafeDestination(installRoot, relative);
            if (!File.Exists(source)) continue;
            string destination = SafeDestination(backupRoot, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(source, destination, true);
        }
        string[] preserveDirectories = { "resources/app/route-library", "resources/app/autobtd6/playthroughs" };
        foreach (string relative in preserveDirectories)
        {
            string source = SafeDestination(installRoot, relative);
            if (!Directory.Exists(source)) continue;
            string destination = SafeDestination(backupRoot, relative);
            CopyDirectory(source, destination);
        }
    }

    private static void CopyDirectory(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (string directory in Directory.GetDirectories(source, "*", SearchOption.AllDirectories))
            Directory.CreateDirectory(Path.Combine(destination, directory.Substring(source.Length).TrimStart(Path.DirectorySeparatorChar)));
        foreach (string file in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string target = Path.Combine(destination, file.Substring(source.Length).TrimStart(Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            File.Copy(file, target, true);
        }
    }

    public virtual void RestoreExistingData(string backupRoot)
    {
        if (!Directory.Exists(backupRoot)) return;
        foreach (string file in Directory.GetFiles(backupRoot, "*", SearchOption.AllDirectories))
        {
            string relative = file.Substring(backupRoot.Length).TrimStart(Path.DirectorySeparatorChar);
            string destination = Path.Combine(installRoot, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(file, destination, true);
        }
    }

    internal static bool IsIdleResponse(string json)
    {
        try {
            var data = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(json);
            object running;
            return data != null && data.TryGetValue("running", out running) && running is bool && !(bool)running;
        } catch { return false; }
    }

    internal static bool IsOwnedAppProcess(string name, string executable, string root)
    {
        if (String.IsNullOrEmpty(executable)) return false;
        string expected = name == "node" ? Path.Combine(root, "resources", "app", "node.exe")
            : name == "Bloons+" ? Path.Combine(root, "Bloons+.exe") : null;
        return expected != null && String.Equals(Path.GetFullPath(executable), Path.GetFullPath(expected), StringComparison.OrdinalIgnoreCase);
    }

    public virtual void CloseInstalledControllers()
    {
        var owned = new List<Process>();
        try {
            foreach (string name in new[] { "node", "Bloons+" }) {
                foreach (Process process in Process.GetProcessesByName(name)) {
                    bool retain = false;
                    try {
                        if (IsOwnedAppProcess(name, process.MainModule.FileName, installRoot)) {
                            owned.Add(process); retain = true;
                        }
                    } catch (InvalidOperationException) { /* Process already exited. */ }
                    finally { if (!retain) process.Dispose(); }
                }
            }
            if (owned.Count == 0) return;
            SetStatus("Checking that the current replay has finished…", InstallerStage.Prepare);
            var request = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:4173/api/farm/status");
            request.Timeout = request.ReadWriteTimeout = 5000;
            request.Proxy = null;
            using (var response = request.GetResponse())
            using (var reader = new StreamReader(response.GetResponseStream())) {
                if (!IsIdleResponse(reader.ReadToEnd()))
                    throw new InvalidOperationException("Finish the current replay before updating Bloons+. No controller was closed.");
            }
            foreach (Process process in owned) {
                if (process.HasExited) continue;
                Log("Closing installed controller " + process.ProcessName + " PID " + process.Id);
                process.Kill();
                if (!process.WaitForExit(10000)) throw new InvalidOperationException("The old Bloons+ controller did not close; update cancelled.");
            }
        } finally { foreach (Process process in owned) process.Dispose(); }
    }

    public virtual void ConfigurePython()
    {
        SetStatus("Checking the existing Python environment…", InstallerStage.Python);
        string appRoot = Path.Combine(installRoot, "resources", "app");
        string python = FindCompatiblePython() ?? Path.Combine(appRoot, "python", "python.exe");
        string venv = Path.Combine(appRoot, ".venv");
        string pipRequirements = Path.Combine(appRoot, "requirements-installer.txt");
        if (!File.Exists(python) || !File.Exists(pipRequirements))
            throw new FileNotFoundException("A compatible Python 3.12 runtime or the bundled fallback is required.");

        string venvPython = Path.Combine(venv, "Scripts", "python.exe");
        bool compatible = File.Exists(venvPython) && ProcessSucceeds(venvPython, "-c \"import sys; assert sys.version_info[:2] == (3,12) and sys.maxsize > 2**32; import pip\"");
        string stamp = Path.Combine(venv, "bloons-requirements.sha256");
        string requirementsHash = HashFile(pipRequirements);
        string installedCheck = "-c \"from importlib import metadata as m;import sys;lines=[x.strip().split('==',1) for x in open(sys.argv[1]) if '==' in x];assert all(m.version(n)==v for n,v in lines)\" " + Quote(pipRequirements);
        string probe = Quote(Path.Combine(appRoot, "autobtd6", "runtime_check.py")) + " --requirements " + Quote(pipRequirements);
        // The stamp is a cache receipt, not evidence that an installed runtime
        // is healthy. Reuse exact pinned packages after all real checks pass,
        // including an older installation with no stamp or a changed stamp.
        if (compatible && ProcessSucceeds(venvPython, installedCheck) && ProcessSucceeds(venvPython, "-m pip check") && ProcessSucceeds(venvPython, probe, 120000)) {
            File.WriteAllText(stamp, requirementsHash);
            SetStatus("Existing Python packages are ready.", InstallerStage.Python, 100);
            return;
        }
        // Package downloads need temporary wheel/extraction space. A healthy
        // environment was already accepted above; check before any repair move.
        string driveRoot = Path.GetPathRoot(installRoot);
        if (new DriveInfo(driveRoot).AvailableFreeSpace < 5L * 1024 * 1024 * 1024)
            throw new IOException("At least 5 GB of free disk space is needed to install the automation runtime.");
        if (Directory.Exists(venv) && !compatible) {
            string preserved = venv + ".repair-" + DateTime.UtcNow.ToString("yyyyMMddHHmmss") + "-" + Guid.NewGuid().ToString("N").Substring(0, 6);
            SetStatus("Preserving an unusable Python environment and rebuilding it…", InstallerStage.Python);
            Directory.Move(venv, preserved);
            Log("Previous environment preserved at " + preserved);
        }
        if (!File.Exists(venvPython)) {
            SetStatus("Creating Bloons+’s private Python environment…", InstallerStage.Python);
            RunInstallerProcess(python, "-m venv --copies " + Quote(venv), appRoot, "Could not create the private Python environment");
        }
        if (!File.Exists(venvPython)) throw new FileNotFoundException("The private Python environment was not created.");
        SetStatus("Downloading Python dependencies (including TensorFlow); this may take a while…", InstallerStage.Python);
        RunInstallerProcess(venvPython, "-m ensurepip --upgrade", appRoot, "Could not repair pip");
        string installArgs = "-m pip install --disable-pip-version-check --no-input --prefer-binary --retries 3 --timeout 60 -r " + Quote(pipRequirements);
        RunInstallerProcess(venvPython, installArgs, appRoot, "Python dependency installation failed");
        SetStatus("Verifying image processing, TensorFlow and keyboard dependencies…", InstallerStage.Python);
        if (!ProcessSucceeds(venvPython, probe, 120000) || !ProcessSucceeds(venvPython, "-m pip check")) {
            SetStatus("Repairing incomplete Python packages…", InstallerStage.Python);
            RunInstallerProcess(venvPython, installArgs + " --force-reinstall", appRoot, "Python package repair failed");
        }
        RunInstallerProcess(venvPython, "-m pip check", appRoot, "Python dependencies are incompatible");
        RunInstallerProcess(venvPython, probe, appRoot, "Automation runtime verification failed");
        File.WriteAllText(stamp, requirementsHash);
    }

    public virtual void EnsureVisualCppRuntime()
    {
        string system = Environment.GetFolderPath(Environment.SpecialFolder.System);
        string runtime = Path.Combine(system, "msvcp140.dll");
        string runtime1 = Path.Combine(system, "msvcp140_1.dll");
        if (File.Exists(runtime) && File.Exists(runtime1)) {
            SetStatus("Microsoft C++ runtime is ready.", InstallerStage.CppRuntime, 100);
            return;
        }
        SetStatus("Downloading the Microsoft C++ runtime required by TensorFlow…", InstallerStage.CppRuntime);
        string installer = Path.Combine(Path.GetTempPath(), "BloonsPlus-vc-redist-" + Guid.NewGuid().ToString("N") + ".exe");
        bool runtimeStarted = false;
        try {
            // .NET Framework can otherwise negotiate legacy TLS on older Windows installs,
            // which makes Microsoft's current aka.ms endpoint fail before setup begins.
            ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072; // TLS 1.2
            var request = (HttpWebRequest)WebRequest.Create("https://aka.ms/vs/17/release/vc_redist.x64.exe");
            request.Timeout = 60000;
            request.ReadWriteTimeout = 15000;
            using (var response = (HttpWebResponse)request.GetResponse())
            using (var source = response.GetResponseStream())
            using (var target = new FileStream(installer, FileMode.Create, FileAccess.Write, FileShare.None)) {
                CopyRuntimeDownload(source, target, response.ContentLength, (received, total) => {
                    Cancellation.ThrowIfCancellationRequested();
                    string amount = (received / 1048576.0).ToString("0.0") + " MB";
                    if (total > 0) amount += " of " + (total / 1048576.0).ToString("0.0") + " MB";
                    SetStatus("Downloading Microsoft C++ runtime: " + amount, InstallerStage.CppRuntime, total > 0 ? (int?)(100 * received / total) : null, "Download", total > 0 ? (long?)received : null, total > 0 ? (long?)total : null);
                });
            }
            SetStatus("Installing the Microsoft C++ runtime (Windows may ask for permission)…", InstallerStage.CppRuntime);
            ProcessStartInfo start = new ProcessStartInfo(installer, "/install /quiet /norestart") {
                UseShellExecute = true, Verb = "runas", WindowStyle = ProcessWindowStyle.Hidden
            };
            ownedProcess.RecordIntent(installer, "microsoft_runtime");
            using (Process child = Process.Start(start)) {
                runtimeStarted = true;
                ownedProcess.Attach(child);
                if (!child.WaitForExit(15 * 60 * 1000))
                    throw new TimeoutException("Microsoft C++ runtime setup has not finished after 15 minutes. It may still be running (process " + child.Id + "). Check Windows installation or permission dialogs before retrying; Bloons+ did not terminate it.");
                if (child.ExitCode != 0 && child.ExitCode != 1638 && child.ExitCode != 3010)
                {
                    ownedProcess.RecordTerminal(child.ExitCode);
                    throw new InvalidOperationException("Microsoft C++ runtime setup exited with code " + child.ExitCode + ".");
                }
                ownedProcess.RecordTerminal(child.ExitCode);
                if (child.ExitCode == 3010) throw new InstallerRestartRequiredException("Microsoft C++ runtime needs a Windows restart. Setup can resume afterward.");
            }
        }
        catch (System.ComponentModel.Win32Exception error) {
            if (!runtimeStarted) ownedProcess.RecordTerminal(-1); // Start was declined, rather than a launched process becoming inaccessible.
            throw new InvalidOperationException("Microsoft C++ runtime installation was cancelled or blocked: " + error.Message);
        }
        finally { try { if (File.Exists(installer)) File.Delete(installer); } catch { } }
        if (!File.Exists(runtime) || !File.Exists(runtime1))
            throw new InvalidOperationException("Microsoft C++ runtime installation finished, but msvcp140.dll and msvcp140_1.dll are still missing. Restart Windows, then run setup again.");
    }

    // Bounded copy also rejects an HTML error page or a truncated download before launch.
    internal static void CopyRuntimeDownload(Stream source, Stream target, long expectedLength, Action<long, long> report)
    {
        const long maximumBytes = 128L * 1024 * 1024;
        if (expectedLength > maximumBytes || expectedLength < -1)
            throw new InvalidDataException("Microsoft runtime download reported an invalid size. Retry setup.");
        var deadline = DateTime.UtcNow.AddMinutes(5);
        var buffer = new byte[64 * 1024];
        long received = 0;
        int first = -1, second = -1;
        var lastReport = DateTime.MinValue;
        while (true) {
            if (DateTime.UtcNow >= deadline)
                throw new TimeoutException("Microsoft runtime download exceeded five minutes. Check your connection and retry setup.");
            int count = source.Read(buffer, 0, buffer.Length);
            if (count == 0) break;
            if (received == 0) first = buffer[0];
            if (received < 2 && received + count >= 2) second = buffer[(int)(1 - received)];
            received += count;
            if (received > maximumBytes || (expectedLength >= 0 && received > expectedLength))
                throw new InvalidDataException("Microsoft runtime download exceeded its expected size. Retry setup.");
            target.Write(buffer, 0, count);
            if (report != null && DateTime.UtcNow - lastReport >= TimeSpan.FromMilliseconds(250)) {
                report(received, expectedLength);
                lastReport = DateTime.UtcNow;
            }
        }
        if (first != 77 || second != 90 || (expectedLength >= 0 && received != expectedLength))
            throw new InvalidDataException("Microsoft runtime download is incomplete or is not an executable. Check your connection and retry setup.");
        if (report != null) report(received, expectedLength);
    }

    private static bool ProcessSucceeds(string file, string arguments, int timeout = 10000)
    {
        try {
            using (Process child = Process.Start(new ProcessStartInfo(file, arguments) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true })) {
                Task<string> output = child.StandardOutput.ReadToEndAsync();
                Task<string> error = child.StandardError.ReadToEndAsync();
                if (!child.WaitForExit(timeout)) { try { child.Kill(); } catch { } return false; }
                Task.WaitAll(output, error);
                return child.ExitCode == 0;
            }
        } catch { return false; }
    }

    private static string FindCompatiblePython()
    {
        string[] candidates = {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python312", "python.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Python312", "python.exe")
        };
        foreach (string candidate in candidates)
            if (File.Exists(candidate) && ProcessSucceeds(candidate, "-c \"import sys; assert sys.version_info[:2] == (3,12) and sys.maxsize > 2**32\"")) return candidate;
        // PATH Python is also accepted, but Windows Store aliases that do not run are ignored.
        foreach (string command in new[] { "py.exe", "python.exe" }) {
            string resolved = ResolvePython(command, command == "py.exe" ? "-3.12 " : "");
            if (resolved != null) return resolved;
        }
        return null;
    }

    private static string ResolvePython(string command, string prefix)
    {
        try {
            using (Process child = Process.Start(new ProcessStartInfo(command, prefix + "-c \"import sys; assert sys.version_info[:2] == (3,12) and sys.maxsize > 2**32; print(sys.executable)\"") {
                UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true })) {
                Task<string> output = child.StandardOutput.ReadToEndAsync();
                Task<string> error = child.StandardError.ReadToEndAsync();
                if (!child.WaitForExit(10000)) { try { child.Kill(); } catch { } return null; }
                Task.WaitAll(output, error);
                string path = output.Result.Trim();
                if (child.ExitCode == 0 && File.Exists(path)) return path;
            }
        } catch { /* not installed */ }
        return null;
    }

    private static string Quote(string value) { return "\"" + value.Replace("\"", "\\\"") + "\""; }

    private void RunInstallerProcess(string executable, string arguments, string workingDirectory, string errorPrefix)
    {
        string lastOutput = "";
        using (var child = ownedProcess.Start(executable, arguments, workingDirectory)) {
            child.BeginRead(line => {
                if (String.IsNullOrWhiteSpace(line)) return;
                lastOutput = line; Log(line);
                if (line.IndexOf("Downloading", StringComparison.OrdinalIgnoreCase) >= 0
                    || line.IndexOf("Installing", StringComparison.OrdinalIgnoreCase) >= 0
                    || line.IndexOf("Successfully installed", StringComparison.OrdinalIgnoreCase) >= 0)
                    SetDetail(line.Length > 80 ? line.Substring(0, 77) + "…" : line);
            }, line => { if (!String.IsNullOrWhiteSpace(line)) { lastOutput = line; Log(line); } });
            if (!child.WaitForExit(45 * 60 * 1000))
                throw new TimeoutException(errorPrefix + ": no completion within 45 minutes. Dependency work may still be running; setup must recover it before retrying. See " + logPath);
            int exitCode = child.ExitCode;
            ownedProcess.RecordTerminal(exitCode); // Requires the whole owned process tree to finish.
            child.FinishReading();
            if (exitCode != 0) throw new InvalidOperationException(errorPrefix + ": " + lastOutput);
        }
    }

    // The Setup bar installs Bloons+ inside the VM from this copy (an installed PC has no dist/ folder).
    public virtual void KeepInstallerCopy()
    {
        string source = Path.GetFullPath(options.InstallerPath);
        string target = Path.Combine(installRoot, "BloonsPlusSetup.exe");
        if (String.Equals(source, Path.GetFullPath(target), StringComparison.OrdinalIgnoreCase)) return;
        SetStatus("Keeping the setup recovery components…", InstallerStage.Files, 100);
        if (!File.Exists(target) || HashFile(source) != HashFile(target)) File.Copy(source, target, true);
    }

    public virtual void SaveSetupIntent()
    {
        if (options.Silent) return;
        string dataRoot = options.DataRoot;
        Directory.CreateDirectory(dataRoot);
        string intent = Path.Combine(dataRoot, "auto-setup.txt");
        if (options.RequestedVmSetup) File.WriteAllText(intent, options.RequestedIsoPath);
        else if (File.Exists(intent)) File.Delete(intent);
    }

    public virtual void CreateStartMenuShortcut()
    {
        string programs = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
        Directory.CreateDirectory(programs);
        string shortcutPath = Path.Combine(programs, "Bloons+.lnk");
        Type shellType = Type.GetTypeFromProgID("WScript.Shell");
        if (shellType == null) return;
        object shell = Activator.CreateInstance(shellType);
        try
        {
            dynamic script = shell;
            dynamic shortcut = script.CreateShortcut(shortcutPath);
            shortcut.TargetPath = Path.Combine(installRoot, "Bloons+.exe");
            shortcut.WorkingDirectory = installRoot;
            shortcut.Description = "Bloons+ BTD6 companion";
            string iconPath = Path.Combine(installRoot, "resources", "app", "bloonsplus.ico");
            if (File.Exists(iconPath)) shortcut.IconLocation = iconPath + ",0";
            shortcut.Save();
        }
        finally { if (Marshal.IsComObject(shell)) Marshal.FinalReleaseComObject(shell); }
    }
}
