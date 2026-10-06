using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

internal sealed class InstallerOptions
{
    public string InstallRoot { get; private set; }
    public string DataRoot { get; private set; }
    public string InstallerPath { get; private set; }
    public bool Silent { get; private set; }
    public string AttemptResultPath { get; private set; }
    public string ResultPath { get { return Path.Combine(DataRoot, "installer-result.txt"); } }
    public string LogPath { get { return Path.Combine(DataRoot, "installer.log"); } }
    public bool RequestedVmSetup { get; set; }
    public string RequestedIsoPath { get; set; }
    public bool LaunchAfterInstall { get; set; }
    public bool StartMenuShortcut { get; set; }
    public InstallerOptions(string root, string dataRoot, string installerPath, bool silent, string attemptToken) {
        InstallRoot = Path.GetFullPath(root); DataRoot = Path.GetFullPath(dataRoot);
        InstallerPath = Path.GetFullPath(installerPath); Silent = silent;
        AttemptResultPath = InstallerEngine.AttemptResultPath(DataRoot, attemptToken);
        RequestedVmSetup = !silent; RequestedIsoPath = "";
        LaunchAfterInstall = StartMenuShortcut = true;
    }
}

internal sealed class InstallerResult
{
    public bool LocalReady { get; internal set; }
    public bool EnvironmentReady { get; internal set; }
    public bool EnvironmentDeferred { get; internal set; }
    public bool RestartRequired { get; internal set; }
    public int ExitCode { get; internal set; }
    public string Receipt { get; internal set; }
    public string Error { get; internal set; }
    public string HumanAction { get; internal set; }
}

internal sealed class InstallerRestartRequiredException : Exception {
    public InstallerRestartRequiredException(string message) : base(message) {}
}

// Owns ordering and receipts. Constructing an engine performs no I/O.
internal sealed class InstallerEngine
{
    private readonly InstallerOptions options;
    private readonly WindowsInstallerOperations operations;
    private readonly object logLock = new object();
    private InstallerProgress current = new InstallerProgress();
    private InstallSession session;
    public InstallerSnapshot CurrentSnapshot { get { return session == null ? null : session.Snapshot; } }
    public event Action<InstallerSnapshot> SnapshotChanged;
    public event Action<InstallerProgress> ProgressChanged;
    public event Action<string> DetailAdded;
    public InstallerEngine(InstallerOptions options, WindowsInstallerOperations operations) {
        if (options == null) throw new ArgumentNullException("options");
        if (operations == null) throw new ArgumentNullException("operations");
        this.options = options; this.operations = operations;
        operations.ProgressChanged += PublishProgress;
        operations.DetailAdded += PublishDetail;
        operations.LogAdded += Log;
        operations.EnvironmentChanged += ObserveEnvironment;
    }
    private void PublishProgress(InstallerProgress state) {
        current = state; Log(state.Message);
        if (session != null && !state.Failed) {
            string phase = state.Stage == InstallerStage.Prepare ? "preflight" : state.Stage == InstallerStage.Files ? "deploying_bloonsplus"
                : state.Stage == InstallerStage.Finish ? "finalizing" : state.Scope == "Download" ? "downloading" : "installing_dependency";
            session.Observe(phase, state.Stage.ToString(), state.Message, state.Numerator, state.Denominator, state.Scope);
            session.ObserveMilestone(state.Stage);
            NotifySnapshot();
        }
        var handler = ProgressChanged; if (handler != null) handler(state);
    }
    private void PublishDetail(string text) {
        Log(text); var handler = DetailAdded; if (handler != null) handler(text);
    }
    private void SetStatus(string text, InstallerStage stage, int? percent = null) {
        var state = new InstallerProgress { Message = text }; state.Update(stage, percent); PublishProgress(state);
    }
    private void SetFailure(string text) {
        var state = new InstallerProgress { Message = text };
        state.Update(current.Stage, current.Percent, current.Scope); state.Fail(); PublishProgress(state);
    }
    internal static string AttemptResultPath(string directory, string token)
    {
        if (token == null) return null;
        Guid parsed;
        if (!Guid.TryParseExact(token, "N", out parsed)) throw new ArgumentException("Invalid installer attempt identifier.");
        return Path.Combine(directory, "installer-result-" + parsed.ToString("N") + ".txt");
    }
    private void WriteAttemptResult(string result)
    {
        if (options.AttemptResultPath == null) return;
        try { Directory.CreateDirectory(Path.GetDirectoryName(options.AttemptResultPath)); File.WriteAllText(options.AttemptResultPath, result); }
        catch (Exception error) { Log("Could not write installer attempt result: " + error.Message); }
    }
    private void WriteResult(string result)
    {
        try { Directory.CreateDirectory(Path.GetDirectoryName(options.ResultPath)); File.WriteAllText(options.ResultPath, result); }
        catch (Exception error) { Log("Could not write installer result: " + error.Message); }
        WriteAttemptResult(result);
    }
    private void Log(string text)
    {
        lock (logLock) {
            try { Directory.CreateDirectory(Path.GetDirectoryName(options.LogPath)); File.AppendAllText(options.LogPath, DateTime.UtcNow.ToString("o") + " " + text + Environment.NewLine); } catch { }
        }
    }

    internal static FileStream AcquireInstallLock(string root)
    {
        Directory.CreateDirectory(root);
        try {
            // Keep this file after release: deleting it could split ownership
            // between two installers that opened different file instances.
            var ownership = new FileStream(Path.Combine(root, ".bloons-install.lock"),
                FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            try { new OwnedProcess(root).RequireIdle(); return ownership; }
            catch { ownership.Dispose(); throw; }
        } catch (IOException error) {
            int code = error.HResult & 0xffff;
            if (code == 32 || code == 33)
                throw new InvalidOperationException("Another Bloons+ installer is working on this installation. Wait for it to finish, then retry.", error);
            throw;
        }
    }

    public Task<InstallerResult> RunAsync(CancellationToken cancellation) {
        return Task.Run(() => Run(cancellation), cancellation);
    }
    private void NotifySnapshot() { var handler = SnapshotChanged; if (handler != null) handler(CurrentSnapshot); }
    private void ObserveEnvironment(System.Collections.Generic.Dictionary<string, object> value) {
        object field;
        string phase = value.TryGetValue("phase", out field) ? field as string : null;
        string status = value.TryGetValue("status", out field) ? field as string : "Checking environment";
        string step = value.TryGetValue("step", out field) ? field as string : null;
        if (phase == "complete") phase = "validating";
        session.Observe(phase, step, status, null, null, null);
        session.SetHumanAction(value.TryGetValue("humanAction", out field) ? field as string : null);
        if (value.TryGetValue("completedWeight", out field)) session.ObserveEnvironmentWeight(Convert.ToInt32(field));
        if (phase == "restart_required") session.RequireRestart(status);
        NotifySnapshot();
        var progress = new InstallerProgress { Message = status }; progress.Update(InstallerStage.Finish, null);
        var handler = ProgressChanged; if (handler != null) handler(progress);
    }
    private InstallerResult FinishEnvironment() {
        var environment = operations.ConfigureEnvironment(session.Snapshot.SessionId);
        if (!environment.Ready) {
            session.Observe(environment.RestartRequired ? "restart_required" : "validating", "environment", environment.Status, null, null, null);
            session.SetHumanAction(environment.HumanAction);
            NotifySnapshot();
            return new InstallerResult { LocalReady = true, Receipt = "APP_READY", HumanAction = environment.HumanAction,
                RestartRequired = environment.RestartRequired, ExitCode = environment.RestartRequired ? 3010 : 0 };
        }
        session.Observe("validating", "environment", "Environment readiness verified", null, null, null);
        session.MarkValidated(true, true); session.Complete();
        if (options.LaunchAfterInstall) operations.LaunchApp();
        WriteResult("OK"); NotifySnapshot();
        return new InstallerResult { LocalReady = true, EnvironmentReady = true, Receipt = "OK", ExitCode = 0 };
    }
    public Task<InstallerResult> ResumeEnvironmentAsync(CancellationToken cancellation) {
        return Task.Run(() => {
            if (session == null || !session.Snapshot.AppValidated || !session.Snapshot.EnvironmentRequired)
                throw new InvalidOperationException("Validated local installation is required before environment resume.");
            using (AcquireInstallLock(options.InstallRoot)) {
                operations.Cancellation = cancellation;
                try { return FinishEnvironment(); }
                catch (Exception error) {
                    Log(error.ToString()); session.Observe("recovering", "environment", "Setup connection needs attention. Reconnect and continue.", null, null, null);
                    session.SetHumanAction("retry"); NotifySnapshot();
                    return new InstallerResult { LocalReady = true, Receipt = "APP_READY", Error = error.Message, HumanAction = "retry" };
                }
            }
        }, cancellation);
    }
    private InstallerResult Run(CancellationToken cancellation)
    {
        string tempZip = Path.Combine(Path.GetTempPath(), "BloonsPlus-" + Guid.NewGuid().ToString("N") + ".zip");
        string backupRoot = Path.Combine(Path.GetTempPath(), "BloonsPlus-data-" + Guid.NewGuid().ToString("N"));
        bool installed = false;
        bool filesStarted = false;
        FileStream installLock = null;
        try {
            installLock = AcquireInstallLock(options.InstallRoot);
            operations.Cancellation = cancellation;
            session = InstallSession.LoadOrCreate(options.InstallRoot, "install", !options.Silent && options.RequestedVmSetup);
            if (session.Snapshot.Phase == "restart_required"
                && (String.IsNullOrEmpty(session.Snapshot.RestartBootIdentity) || String.IsNullOrEmpty(OwnedProcess.CurrentBootIdentity)
                    || session.Snapshot.RestartBootIdentity == OwnedProcess.CurrentBootIdentity))
                throw new InstallerRestartRequiredException("Restart Windows before resuming setup. Required reboot has not been confirmed.");
            session.Observe("preflight", "ownership", "Checking installation", null, null, null);
            WriteResult("RUNNING");
            cancellation.ThrowIfCancellationRequested();
            operations.CloseInstalledControllers();
            if (!String.IsNullOrEmpty(session.Snapshot.BackupPath)) {
                string priorBackup = session.Snapshot.BackupPath;
                session.RetainBackup(priorBackup); // Validate containment before touching a retained path.
                operations.RestoreExistingData(priorBackup);
            }
            SetStatus("Reading embedded app package…", InstallerStage.Prepare);
            operations.ReadEmbeddedPackage(tempZip);
            cancellation.ThrowIfCancellationRequested();
            session.RetainBackup(backupRoot);
            operations.BackupExistingData(backupRoot);
            filesStarted = true;
            operations.InstallAppFiles(tempZip);
            cancellation.ThrowIfCancellationRequested();
            operations.RestoreExistingData(backupRoot);
            operations.KeepInstallerCopy(); // Guest ownership probes can read the current recovery observer even after a parent exit.
            SetStatus("Checking required runtime components…", InstallerStage.CppRuntime);
            operations.EnsureVisualCppRuntime();
            cancellation.ThrowIfCancellationRequested();
            operations.ConfigurePython();
            cancellation.ThrowIfCancellationRequested();
            session.Observe("validating", "local_runtime", "App files and runtime verified", null, null, null);
            session.MarkValidated(true, false);
            SetStatus("Creating the app shortcut…", InstallerStage.Finish);
            if (options.StartMenuShortcut) operations.CreateStartMenuShortcut();
            operations.SaveSetupIntent();
            if (session.Snapshot.EnvironmentRequired) {
                installed = true;
                var environment = FinishEnvironment();
                WriteResult(environment.Receipt);
                return environment;
            }
            SetStatus(options.LaunchAfterInstall ? "Bloons+ is installed. Launching the app…" : "Bloons+ is installed.", InstallerStage.Finish, 100);
            if (options.LaunchAfterInstall) operations.LaunchApp();
            installed = true;
            WriteResult("OK");
            if (!session.Snapshot.EnvironmentRequired) session.Complete();
            NotifySnapshot();
            return new InstallerResult { LocalReady = true, Receipt = "OK", ExitCode = 0,
                EnvironmentDeferred = !options.Silent && !options.RequestedVmSetup };
        } catch (Exception error) {
            Log(error.ToString());
            bool restart = error is InstallerRestartRequiredException;
            string receipt = restart ? "RESTART_REQUIRED: " + error.Message : "ERROR: " + error.Message;
            if (installLock != null) WriteResult(receipt);
            else WriteAttemptResult("ERROR: " + error.Message);
            // Never restore files beneath a surviving package installer.
            if (filesStarted && installLock != null && new OwnedProcess(options.InstallRoot).Observe() == "idle") {
                try { operations.RestoreExistingData(backupRoot); }
                catch (Exception restoreError) { Log("Data backup retained at " + backupRoot + ": " + restoreError); }
            }
            SetFailure("Installation failed: " + error.Message);
            if (session != null) {
                if (restart) session.RequireRestart(error.Message);
                else session.Observe(error is OperationCanceledException ? "cancelled" : new OwnedProcess(options.InstallRoot).Observe() == "idle" ? "failed" : "recovering",
                    "recovery", error.Message, null, null, null);
                NotifySnapshot();
            }
            return new InstallerResult { LocalReady = installed, Receipt = receipt, Error = error.Message, ExitCode = restart ? 3010 : 1, RestartRequired = restart, HumanAction = installed ? "retry" : null };
        } finally {
            operations.Dispose();
            if (installLock != null) installLock.Dispose();
            try { if (File.Exists(tempZip)) File.Delete(tempZip); } catch { }
            if (installed) { try { if (Directory.Exists(backupRoot)) Directory.Delete(backupRoot, true); } catch { } }
            // An interrupted update retains its prior app data for recovery.
        }
    }
}
