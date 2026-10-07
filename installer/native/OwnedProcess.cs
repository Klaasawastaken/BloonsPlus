using System;
using System.IO;
using System.Diagnostics;
using System.Web.Script.Serialization;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Reflection;
using System.Collections;

// A launch intent is durable before Start. Unobserved work remains busy, never guessed successful.
internal sealed class OwnedProcess : IDisposable
{
    [StructLayout(LayoutKind.Sequential)] private struct JobAccounting {
        public long totalUser, totalKernel, periodUser, periodKernel;
        public uint faults, totalProcesses, activeProcesses, terminatedProcesses;
    }
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern IntPtr CreateJobObject(IntPtr security, string name);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern IntPtr OpenJobObject(int access, bool inherit, string name);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool QueryInformationJobObject(IntPtr job, int information, out JobAccounting accounting, int size, IntPtr returned);
    [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
    private IntPtr jobHandle;
    internal sealed class Receipt {
        public string Executable { get; set; }
        public string Kind { get; set; }
        public int? Pid { get; set; }
        public long? CreatedUtcTicks { get; set; }
        public bool TerminalObserved { get; set; }
        public int? ExitCode { get; set; }
        public string JobName { get; set; }
        public string BootIdentity { get; set; }
    }
    private readonly string file;
    private readonly JavaScriptSerializer serializer = new JavaScriptSerializer();
    private readonly Func<string> bootIdentity;
    private static readonly Lazy<string> MachineBoot = new Lazy<string>(ReadMachineBoot);
    internal static string CurrentBootIdentity { get { return MachineBoot.Value; } }
    public OwnedProcess(string root, Func<string> bootIdentity = null) {
        file = Path.Combine(Path.GetFullPath(root), ".bloons-setup", "owned-process.json");
        this.bootIdentity = bootIdentity ?? (() => MachineBoot.Value);
    }
    private static string ReadMachineBoot() {
        // System.Management is part of the installed Framework, not a bundled runtime.
        // A timed-out or unavailable WMI observation stays unknown.
        var observation = Task.Run(() => {
            try {
                var assembly = Assembly.Load("System.Management, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a");
                using (var searcher = (IDisposable)Activator.CreateInstance(assembly.GetType("System.Management.ManagementObjectSearcher"),
                    new object[] { "SELECT LastBootUpTime FROM Win32_OperatingSystem" })) {
                    dynamic query = searcher; query.Options.Timeout = TimeSpan.FromSeconds(3);
                    using (var rows = (IDisposable)query.Get()) {
                        foreach (dynamic row in (IEnumerable)rows) {
                            string raw = Convert.ToString(row["LastBootUpTime"]);
                            var converter = assembly.GetType("System.Management.ManagementDateTimeConverter").GetMethod("ToDateTime");
                            return ((DateTime)converter.Invoke(null, new object[] { raw })).ToUniversalTime().Ticks.ToString(System.Globalization.CultureInfo.InvariantCulture);
                        }
                    }
                }
            } catch { }
            return (string)null;
        });
        return observation.Wait(3500) ? observation.Result : null;
    }
    private Receipt Read() {
        if (!File.Exists(file)) return null;
        if (new FileInfo(file).Length > 64 * 1024) throw new InvalidDataException("Dependency receipt is invalid.");
        var receipt = serializer.Deserialize<Receipt>(File.ReadAllText(file));
        if (receipt == null || String.IsNullOrEmpty(receipt.Executable)) throw new InvalidDataException("Dependency receipt is invalid.");
        return receipt;
    }
    private void Write(Receipt receipt) { InstallSession.AtomicWrite(file, serializer.Serialize(receipt)); }
    public void RecordIntent(string executable, string kind) {
        Write(new Receipt { Executable = Path.GetFullPath(executable), Kind = kind, BootIdentity = bootIdentity() });
    }
    public void Attach(Process process) {
        var receipt = Read();
        if (receipt == null) throw new InvalidOperationException("Dependency launch intent is missing.");
        receipt.Pid = process.Id; receipt.CreatedUtcTicks = process.StartTime.ToUniversalTime().Ticks;
        Write(receipt);
    }
    public void RecordTerminal(int exitCode) {
        var receipt = Read();
        if (receipt == null) throw new InvalidOperationException("Dependency launch intent is missing.");
        receipt.ExitCode = exitCode;
        int outstanding = 0;
        if (!String.IsNullOrEmpty(receipt.JobName)) {
            var deadline = DateTime.UtcNow.AddSeconds(1);
            do {
                outstanding = JobCount(receipt.JobName);
                if (outstanding <= 0 || DateTime.UtcNow >= deadline) break;
                Thread.Sleep(25); // Job accounting can lag the direct process exit signal.
            } while (true);
        }
        if (outstanding != 0) {
            Write(receipt);
            throw new InvalidOperationException("Dependency descendants are still running or cannot be observed. Setup must wait before recovery.");
        }
        receipt.TerminalObserved = true; Write(receipt);
    }
    public InstallerChildProcess Start(string executable, string arguments, string directory) {
        string name = "BloonsPlusInstall." + Guid.NewGuid().ToString("N");
        if (jobHandle != IntPtr.Zero) { CloseHandle(jobHandle); jobHandle = IntPtr.Zero; }
        jobHandle = CreateJobObject(IntPtr.Zero, name);
        if (jobHandle == IntPtr.Zero) throw new Win32Exception();
        Write(new Receipt { Executable = Path.GetFullPath(executable), Kind = "python_dependency", JobName = name, BootIdentity = bootIdentity() });
        InstallerChildProcess child;
        try {
            // The query observer must retain the job before any package child
            // can start. It survives this installer's UI/process interruption.
            using (var observer = InstallerProcessObserver.Start(Path.GetDirectoryName(Path.GetDirectoryName(file)), name))
                child = InstallerChildProcess.Start(executable, arguments, directory, jobHandle);
        }
        catch { RecordTerminal(-1); throw; }
        using (var process = Process.GetProcessById(child.Id)) Attach(process);
        return child;
    }
    private static int JobCount(string name) {
        Guid identity;
        if (!name.StartsWith("BloonsPlusInstall.", StringComparison.Ordinal) || !Guid.TryParseExact(name.Substring(18), "N", out identity)) return -1;
        IntPtr handle = OpenJobObject(4, false, name); // Query only; never terminate a job or its children.
        if (handle == IntPtr.Zero) return -1; // A closed observer cannot prove an unobservable process tree empty.
        try {
            JobAccounting data;
            return QueryInformationJobObject(handle, 1, out data, Marshal.SizeOf(typeof(JobAccounting)), IntPtr.Zero) ? (int)data.activeProcesses : -1;
        } finally { CloseHandle(handle); }
    }
    internal static bool Matches(int pid, long createdUtcTicks, string executable) {
        try {
            using (var process = Process.GetProcessById(pid))
                return !process.HasExited && process.StartTime.ToUniversalTime().Ticks == createdUtcTicks
                    && String.Equals(Path.GetFullPath(process.MainModule.FileName), Path.GetFullPath(executable), StringComparison.OrdinalIgnoreCase);
        } catch { return false; }
    }
    public string Observe() {
        try {
            var receipt = Read();
            if (receipt == null || receipt.TerminalObserved) return "idle";
            if (receipt.Pid.HasValue && receipt.CreatedUtcTicks.HasValue && Matches(receipt.Pid.Value, receipt.CreatedUtcTicks.Value, receipt.Executable)) return "running";
            string currentBoot = bootIdentity();
            if (!String.IsNullOrEmpty(receipt.BootIdentity) && !String.IsNullOrEmpty(currentBoot) && receipt.BootIdentity != currentBoot) return "idle";
            if (!String.IsNullOrEmpty(receipt.JobName)) {
                int count = JobCount(receipt.JobName);
                if (count > 0) return "running";
                if (count == 0 && receipt.ExitCode.HasValue) return "idle";
                if (receipt.Pid.HasValue && receipt.CreatedUtcTicks.HasValue && Matches(receipt.Pid.Value, receipt.CreatedUtcTicks.Value, receipt.Executable)) return "running";
                if (InstallerProcessObserver.ObservedEmpty(Path.GetDirectoryName(Path.GetDirectoryName(file)), receipt.JobName)) return "idle";
                return "unknown";
            }
            return receipt.Pid.HasValue && receipt.CreatedUtcTicks.HasValue && Matches(receipt.Pid.Value, receipt.CreatedUtcTicks.Value, receipt.Executable)
                ? "running" : "unknown";
        } catch { return "unknown"; } // Unreadable state never permits another mutating process.
    }
    public void RequireIdle() {
        if (Observe() != "idle") throw new InvalidOperationException(
            "An earlier dependency operation is running or needs recovery. No second installation was started. Check setup details before resuming.");
    }
    public void Dispose() { if (jobHandle != IntPtr.Zero) { CloseHandle(jobHandle); jobHandle = IntPtr.Zero; } }
}
