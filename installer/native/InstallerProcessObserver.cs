using System;
using System.IO;
using System.Diagnostics;
using System.Globalization;
using System.Text;
using System.Threading;
using System.Runtime.InteropServices;
using System.Web.Script.Serialization;

// A transient mode of this installer, outside the dependency's job. It retains
// query ownership when the UI exits; it never kills processes or installs files.
internal sealed class InstallerProcessObserver : IDisposable
{
    private const string Mode = "/observe-dependency";
    [StructLayout(LayoutKind.Sequential)] private struct JobAccounting {
        public long totalUser, totalKernel, periodUser, periodKernel;
        public uint faults, totalProcesses, activeProcesses, terminatedProcesses;
    }
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr OpenJobObject(int access, bool inherit, string name);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool QueryInformationJobObject(IntPtr job, int information, out JobAccounting accounting, int size, IntPtr returned);
    [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
    private readonly EventWaitHandle ready, launched;
    internal sealed class EmptyObservation {
        public string JobName { get; set; }
        public bool EmptyObserved { get; set; }
    }
    private InstallerProcessObserver(string name) {
        ready = new EventWaitHandle(false, EventResetMode.ManualReset, name + ".Ready");
        launched = new EventWaitHandle(false, EventResetMode.ManualReset, name + ".Launched");
    }
    private static bool ValidName(string name) {
        Guid id;
        return name != null && name.StartsWith("BloonsPlusInstall.", StringComparison.Ordinal)
            && Guid.TryParseExact(name.Substring(18), "N", out id);
    }
    private static string ObservationFile(string root, string name) {
        if (!ValidName(name)) throw new InvalidDataException("Invalid dependency job identity.");
        return Path.Combine(Path.GetFullPath(root), ".bloons-setup", "process-observations", name + ".json");
    }
    internal static bool ObservedEmpty(string root, string name) {
        try {
            string file = ObservationFile(root, name);
            if (!File.Exists(file) || new FileInfo(file).Length > 4096) return false;
            var observation = new JavaScriptSerializer().Deserialize<EmptyObservation>(File.ReadAllText(file));
            return observation != null && observation.EmptyObserved && observation.JobName == name;
        } catch { return false; }
    }
    internal static InstallerProcessObserver Start(string root, string name) {
        if (!ValidName(name)) throw new InvalidDataException("Invalid dependency job identity.");
        var observer = new InstallerProcessObserver(name);
        try {
            using (var parent = Process.GetCurrentProcess()) {
                string arguments = Mode + " " + Convert.ToBase64String(Encoding.UTF8.GetBytes(Path.GetFullPath(root)))
                    + " " + name + " " + parent.Id.ToString(CultureInfo.InvariantCulture)
                    + " " + parent.StartTime.ToUniversalTime().Ticks.ToString(CultureInfo.InvariantCulture);
                using (var process = Process.Start(new ProcessStartInfo(parent.MainModule.FileName, arguments) {
                    UseShellExecute = false, CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden
                })) {
                    var wait = Stopwatch.StartNew();
                    while (!observer.ready.WaitOne(50)) {
                        if (process.HasExited || wait.ElapsedMilliseconds >= 10000)
                            throw new InvalidOperationException("Dependency observer did not become ready. No dependency was started.");
                    }
                }
            }
            return observer;
        } catch { observer.Dispose(); throw; }
    }
    public void Dispose() {
        // This launch attempt cannot create additional job members after this
        // signal, including when CreateProcess failed. The observer owns its
        // own event and job handles and keeps waiting for existing children.
        launched.Set(); launched.Dispose(); ready.Dispose();
    }
    internal static bool TryRun(string[] args) {
        if (args.Length == 0 || args[0] != Mode) return false;
        try { Run(args); }
        catch { Environment.ExitCode = 1; } // No empty evidence on an observation failure.
        return true;
    }
    private static void Run(string[] args) {
        if (args.Length != 5 || args[1].Length > 16384 || !ValidName(args[2]))
            throw new InvalidDataException("Invalid observer arguments.");
        string root = Path.GetFullPath(Encoding.UTF8.GetString(Convert.FromBase64String(args[1]))), name = args[2];
        int pid = Int32.Parse(args[3], CultureInfo.InvariantCulture);
        long ticks = Int64.Parse(args[4], CultureInfo.InvariantCulture);
        using (var parent = Process.GetProcessById(pid)) {
            if (parent.StartTime.ToUniversalTime().Ticks != ticks)
                throw new InvalidDataException("Installer owner identity changed.");
            // Retain the exact parent handle before announcing readiness. PID
            // reuse later cannot make another process look like this owner.
            IntPtr parentHandle = parent.Handle;
            IntPtr job = OpenJobObject(4, false, name);
            if (job == IntPtr.Zero) throw new InvalidOperationException("Dependency job is unavailable.");
            try {
                using (var ready = EventWaitHandle.OpenExisting(name + ".Ready"))
                using (var launched = EventWaitHandle.OpenExisting(name + ".Launched")) {
                    ready.Set();
                    while (true) {
                        // Before the launch signal the parent may still add its
                        // single dependency. Parent exit also closes that window.
                        if (launched.WaitOne(0) || parent.WaitForExit(0)) {
                            JobAccounting data;
                            if (!QueryInformationJobObject(job, 1, out data, Marshal.SizeOf(typeof(JobAccounting)), IntPtr.Zero))
                                throw new InvalidOperationException("Dependency job cannot be observed.");
                            if (data.activeProcesses == 0) {
                                InstallSession.AtomicWrite(ObservationFile(root, name), new JavaScriptSerializer().Serialize(
                                    new EmptyObservation { JobName = name, EmptyObserved = true }));
                                return;
                            }
                        }
                        Thread.Sleep(100);
                    }
                }
            } finally { CloseHandle(job); }
        }
    }
}
