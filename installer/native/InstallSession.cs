using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;

internal sealed class InstallSession
{
    private static readonly string[] Phases = {
        "idle", "preflight", "downloading", "installing_dependency", "enabling_feature", "restart_required",
        "configuring_vm", "starting_vm", "configuring_guest", "configuring_ssh", "deploying_bloonsplus",
        "validating", "finalizing", "complete", "recovering", "failed", "cancelled"
    };
    private readonly string checkpoint;
    private readonly object stateLock = new object();
    private InstallerSnapshot state;
    private readonly JavaScriptSerializer serializer = new JavaScriptSerializer();
    public InstallerSnapshot Snapshot {
        get { lock (stateLock) return serializer.Deserialize<InstallerSnapshot>(serializer.Serialize(state)); }
    }
    private InstallSession(string root) { checkpoint = Path.Combine(Path.GetFullPath(root), ".bloons-setup", "session.json"); }
    public static InstallSession LoadOrCreate(string root, string operation, bool environmentRequired)
    {
        if (!new[] { "install", "update", "repair", "resume" }.Contains(operation)) throw new ArgumentException("Invalid setup operation.");
        var session = new InstallSession(root);
        if (File.Exists(session.checkpoint)) {
            if (new FileInfo(session.checkpoint).Length > 256 * 1024) throw new InvalidDataException("Setup checkpoint is too large.");
            session.state = session.serializer.Deserialize<InstallerSnapshot>(File.ReadAllText(session.checkpoint));
            Guid id;
            if (session.state == null || session.state.ProtocolVersion != 1 || !Guid.TryParseExact(session.state.SessionId, "N", out id)
                || session.state.Sequence < 0 || session.state.PlanWeight != 100 || !Phases.Contains(session.state.Phase))
                throw new InvalidDataException("Setup checkpoint cannot be trusted. Keep it for diagnostics before repairing setup.");
            if (session.state.Phase != "complete") {
                if (session.state.EnvironmentRequired != environmentRequired)
                    throw new InvalidOperationException("Resume the saved setup choices before changing its plan.");
                return session;
            }
        }
        session.state = new InstallerSnapshot { ProtocolVersion = 1, SessionId = Guid.NewGuid().ToString("N"),
            Operation = operation, Phase = "idle", Status = "Ready to install", PlanWeight = 100,
            EnvironmentRequired = environmentRequired, Indeterminate = true };
        session.SaveCheckpoint();
        return session;
    }
    public bool TryCommand(string sessionId, long sequence, string action)
    {
        lock (stateLock) {
            if (sessionId != state.SessionId || sequence != state.Sequence) return false;
            if (action == "start" && state.Phase == "idle") state.Phase = "preflight";
            else if ((action == "resume" || action == "retry") && new[] { "failed", "cancelled", "restart_required", "recovering" }.Contains(state.Phase)) {
                state.Phase = "recovering"; state.Error = null; state.HumanAction = null;
                state.AppValidated = state.EnvironmentValidated = false;
            } else if (action == "restart_later" && state.Phase == "restart_required") state.RestartDeferred = true;
            else if (action == "cancel" && !new[] { "idle", "complete", "cancelled" }.Contains(state.Phase)) {
                state.Phase = "cancelled"; state.Status = "Setup paused; active work must finish before retrying.";
            } else return false;
            SaveCheckpoint(); return true;
        }
    }
    public void Observe(string phase, string step, string status, long? numerator, long? denominator, string scope)
    {
        if (!Phases.Contains(phase) || phase == "complete") throw new ArgumentException("Invalid observed setup phase.");
        if (numerator.HasValue != denominator.HasValue || (numerator.HasValue && (numerator < 0 || denominator <= 0 || numerator > denominator)))
            throw new ArgumentException("Invalid measured progress.");
        lock (stateLock) {
            if (state.Phase == "complete") throw new InvalidOperationException("A completed setup session is immutable.");
            state.Phase = phase; state.Step = step; state.Status = status;
            state.StageNumerator = numerator; state.StageDenominator = denominator;
            state.ProgressScope = scope; state.Indeterminate = !numerator.HasValue;
            state.Error = phase == "failed" || phase == "recovering" ? status : null;
            state.HumanAction = phase == "recovering" ? "check_dependency" : null;
            SaveCheckpoint();
        }
    }
    public void RetainBackup(string path) {
        string canonical = Path.GetFullPath(path);
        string temporaryRoot = Path.GetFullPath(Path.GetTempPath()).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        Guid identity;
        string name = Path.GetFileName(canonical);
        if (!String.Equals(Path.GetDirectoryName(canonical) + Path.DirectorySeparatorChar, temporaryRoot, StringComparison.OrdinalIgnoreCase)
            || !name.StartsWith("BloonsPlus-data-", StringComparison.Ordinal)
            || !Guid.TryParseExact(name.Substring(16), "N", out identity)) throw new ArgumentException("Invalid setup backup path.");
        lock (stateLock) { state.BackupPath = canonical; SaveCheckpoint(); }
    }
    public void SetHumanAction(string action) {
        lock (stateLock) { state.HumanAction = action; SaveCheckpoint(); }
    }
    public void ObserveMilestone(InstallerStage stage) {
        int[] weights = { 0, 5, 30, 15, 45, 5 };
        int completed = 0; for (int index = 1; index < (int)stage; index++) completed += weights[index];
        lock (stateLock) { state.CompletedWeight = state.EnvironmentRequired ? completed * 60 / 100 : completed; SaveCheckpoint(); }
    }
    public void ObserveEnvironmentWeight(int completed) {
        if (completed < 0 || completed > 100) throw new ArgumentOutOfRangeException("completed");
        lock (stateLock) { state.CompletedWeight = 60 + completed * 35 / 100; SaveCheckpoint(); }
    }
    public void MarkValidated(bool app, bool environment)
    {
        lock (stateLock) {
            if (state.Phase != "validating") throw new InvalidOperationException("Validation requires a fresh validating observation.");
            state.AppValidated = app; state.EnvironmentValidated = environment; SaveCheckpoint();
        }
    }
    public void RequireRestart(string status)
    {
        bool alreadyRequired = Snapshot.Phase == "restart_required";
        Observe("restart_required", "windows", status, null, null, null);
        lock (stateLock) {
            state.HumanAction = "restart_windows";
            if (!alreadyRequired) { state.RestartDeferred = false; state.RestartBootIdentity = OwnedProcess.CurrentBootIdentity; }
            SaveCheckpoint();
        }
    }
    public void Complete()
    {
        lock (stateLock) {
            if (!state.AppValidated || (state.EnvironmentRequired && !state.EnvironmentValidated))
                throw new InvalidOperationException("Selected setup components must be validated before completion.");
            state.Phase = "complete"; state.Status = state.EnvironmentRequired ? "Bloons+ is ready" : "App installed";
            state.CompletedWeight = state.PlanWeight; state.Indeterminate = false;
            state.StageNumerator = state.StageDenominator = 1; state.HumanAction = null; SaveCheckpoint();
        }
    }
    public void SaveCheckpoint()
    {
        lock (stateLock) {
            state.Sequence++; state.ObservedAt = DateTime.UtcNow.ToString("o");
            AtomicWrite(checkpoint, serializer.Serialize(state));
        }
    }
    internal static void AtomicWrite(string destination, string text)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(destination));
        string temporary = destination + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try {
            using (var output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None)) {
                byte[] bytes = Encoding.UTF8.GetBytes(text); output.Write(bytes, 0, bytes.Length); output.Flush(true);
            }
            if (File.Exists(destination)) File.Replace(temporary, destination, null);
            else File.Move(temporary, destination);
        } finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
}
