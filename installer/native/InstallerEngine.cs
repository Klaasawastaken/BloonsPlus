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
}

// Owns ordering and receipts. Constructing an engine performs no I/O.
internal sealed class InstallerEngine
{
    private readonly InstallerOptions options;
    private readonly WindowsInstallerOperations operations;
    private readonly object logLock = new object();
    private InstallerProgress current = new InstallerProgress();
    public event Action<InstallerProgress> ProgressChanged;
    public event Action<string> DetailAdded;
    public InstallerEngine(InstallerOptions options, WindowsInstallerOperations operations) {
        if (options == null) throw new ArgumentNullException("options");
        if (operations == null) throw new ArgumentNullException("operations");
        this.options = options; this.operations = operations;
        operations.ProgressChanged += PublishProgress;
        operations.DetailAdded += PublishDetail;
        operations.LogAdded += Log;
    }
    private void PublishProgress(InstallerProgress state) {
        current = state; Log(state.Message);
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
            return new FileStream(Path.Combine(root, ".bloons-install.lock"),
                FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
        } catch (IOException error) {
            int code = error.HResult & 0xffff;
            if (code == 32 || code == 33)
                throw new InvalidOperationException("Another Bloons+ installer is working on this installation. Wait for it to finish, then retry.", error);
            throw;
        }
    }

    public Task<InstallerResult> RunAsync(CancellationToken cancellation) {
        return Task.Run((Func<InstallerResult>)Run, cancellation);
    }
    private InstallerResult Run()
    {
        string tempZip = Path.Combine(Path.GetTempPath(), "BloonsPlus-" + Guid.NewGuid().ToString("N") + ".zip");
        string backupRoot = Path.Combine(Path.GetTempPath(), "BloonsPlus-data-" + Guid.NewGuid().ToString("N"));
        bool installed = false;
        FileStream installLock = null;
        try {
            installLock = AcquireInstallLock(options.InstallRoot);
            WriteResult("RUNNING");
            operations.CloseInstalledControllers();
            SetStatus("Reading embedded app package…", InstallerStage.Prepare);
            operations.ReadEmbeddedPackage(tempZip);
            operations.BackupExistingData(backupRoot);
            operations.InstallAppFiles(tempZip);
            operations.RestoreExistingData(backupRoot);
            SetStatus("Checking required runtime components…", InstallerStage.CppRuntime);
            operations.EnsureVisualCppRuntime();
            operations.ConfigurePython();
            SetStatus("Creating the app shortcut…", InstallerStage.Finish);
            if (options.StartMenuShortcut) operations.CreateStartMenuShortcut();
            operations.KeepInstallerCopy();
            operations.SaveSetupIntent();
            SetStatus(options.LaunchAfterInstall ? "Bloons+ is installed. Launching the app…" : "Bloons+ is installed.", InstallerStage.Finish, 100);
            if (options.LaunchAfterInstall) operations.LaunchApp();
            installed = true;
            WriteResult("OK");
            return new InstallerResult { LocalReady = true, Receipt = "OK", ExitCode = 0,
                EnvironmentDeferred = !options.Silent && !options.RequestedVmSetup };
        } catch (Exception error) {
            Log(error.ToString());
            if (installLock != null) WriteResult("ERROR: " + error.Message);
            else WriteAttemptResult("ERROR: " + error.Message);
            if (installLock != null) {
                try { operations.RestoreExistingData(backupRoot); }
                catch (Exception restoreError) { Log("Data backup retained at " + backupRoot + ": " + restoreError); }
            }
            SetFailure("Installation failed: " + error.Message);
            return new InstallerResult { LocalReady = false, Receipt = "ERROR: " + error.Message, Error = error.Message, ExitCode = 1 };
        } finally {
            if (installLock != null) installLock.Dispose();
            try { if (File.Exists(tempZip)) File.Delete(tempZip); } catch { }
            if (installed) { try { if (Directory.Exists(backupRoot)) Directory.Delete(backupRoot, true); } catch { } }
            // An interrupted update retains its prior app data for recovery.
        }
    }
}
