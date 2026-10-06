using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

// Create directly inside a job: no interval in which a dependency can spawn an untracked child.
internal sealed class InstallerChildProcess : IDisposable
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct StartupInfo {
        public int cb; public string reserved, desktop, title;
        public int x, y, width, height, xChars, yChars, fill, flags;
        public short show, reservedBytes; public IntPtr reservedPointer, stdin, stdout, stderr;
    }
    [StructLayout(LayoutKind.Sequential)] private struct StartupInfoEx { public StartupInfo info; public IntPtr attributes; }
    [StructLayout(LayoutKind.Sequential)] private struct ProcessInfo { public IntPtr process, thread; public int pid, threadId; }
    [StructLayout(LayoutKind.Sequential)] private struct SecurityAttributes { public int size; public IntPtr descriptor; public int inherit; }
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool CreatePipe(out IntPtr read, out IntPtr write, ref SecurityAttributes security, int size);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool SetHandleInformation(IntPtr handle, int mask, int flags);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool InitializeProcThreadAttributeList(IntPtr attributes, int count, int flags, ref IntPtr size);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool UpdateProcThreadAttribute(IntPtr attributes, int flags, IntPtr attribute, IntPtr value, IntPtr size, IntPtr previous, IntPtr returnedSize);
    [DllImport("kernel32.dll")] private static extern void DeleteProcThreadAttributeList(IntPtr attributes);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern bool CreateProcess(string application, StringBuilder command, IntPtr processSecurity, IntPtr threadSecurity, bool inherit, int flags, IntPtr environment, string directory, ref StartupInfoEx startup, out ProcessInfo process);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern int WaitForSingleObject(IntPtr handle, int timeout);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool GetExitCodeProcess(IntPtr process, out int code);
    [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
    private IntPtr processHandle;
    private readonly StreamReader output, error;
    private Task outputTask, errorTask;
    public int Id { get; private set; }
    public int ExitCode {
        get { int code; if (!GetExitCodeProcess(processHandle, out code)) throw new Win32Exception(); return code; }
    }
    private InstallerChildProcess(ProcessInfo process, IntPtr outputRead, IntPtr errorRead) {
        processHandle = process.process; Id = process.pid;
        output = new StreamReader(new FileStream(new SafeFileHandle(outputRead, true), FileAccess.Read));
        error = new StreamReader(new FileStream(new SafeFileHandle(errorRead, true), FileAccess.Read));
    }
    public static InstallerChildProcess Start(string executable, string arguments, string directory, IntPtr job)
    {
        IntPtr readOutput = IntPtr.Zero, writeOutput = IntPtr.Zero, readError = IntPtr.Zero, writeError = IntPtr.Zero;
        IntPtr attributes = IntPtr.Zero, jobs = IntPtr.Zero, handles = IntPtr.Zero;
        bool initialized = false;
        try {
            var security = new SecurityAttributes { size = Marshal.SizeOf(typeof(SecurityAttributes)), inherit = 1 };
            if (!CreatePipe(out readOutput, out writeOutput, ref security, 0) || !CreatePipe(out readError, out writeError, ref security, 0)) throw new Win32Exception();
            if (!SetHandleInformation(readOutput, 1, 0) || !SetHandleInformation(readError, 1, 0)) throw new Win32Exception();
            IntPtr size = IntPtr.Zero;
            InitializeProcThreadAttributeList(IntPtr.Zero, 2, 0, ref size);
            attributes = Marshal.AllocHGlobal(size);
            if (!InitializeProcThreadAttributeList(attributes, 2, 0, ref size)) throw new Win32Exception();
            initialized = true;
            jobs = Marshal.AllocHGlobal(IntPtr.Size); Marshal.WriteIntPtr(jobs, job);
            handles = Marshal.AllocHGlobal(IntPtr.Size * 2); Marshal.WriteIntPtr(handles, writeOutput); Marshal.WriteIntPtr(handles, IntPtr.Size, writeError);
            if (!UpdateProcThreadAttribute(attributes, 0, new IntPtr(0x2000D), jobs, new IntPtr(IntPtr.Size), IntPtr.Zero, IntPtr.Zero)
                || !UpdateProcThreadAttribute(attributes, 0, new IntPtr(0x20002), handles, new IntPtr(IntPtr.Size * 2), IntPtr.Zero, IntPtr.Zero)) throw new Win32Exception();
            var startup = new StartupInfoEx { attributes = attributes, info = new StartupInfo {
                cb = Marshal.SizeOf(typeof(StartupInfoEx)), flags = 0x100, stdout = writeOutput, stderr = writeError } };
            ProcessInfo process;
            if (!CreateProcess(executable, new StringBuilder("\"" + executable + "\" " + arguments), IntPtr.Zero, IntPtr.Zero, true,
                0x80000 | 0x8000000, IntPtr.Zero, directory, ref startup, out process)) throw new Win32Exception();
            CloseHandle(process.thread);
            var child = new InstallerChildProcess(process, readOutput, readError);
            readOutput = readError = IntPtr.Zero;
            return child;
        } finally {
            foreach (IntPtr handle in new[] {readOutput, writeOutput, readError, writeError}) if (handle != IntPtr.Zero) CloseHandle(handle);
            if (initialized) DeleteProcThreadAttributeList(attributes);
            foreach (IntPtr memory in new[] {attributes, jobs, handles}) if (memory != IntPtr.Zero) Marshal.FreeHGlobal(memory);
        }
    }
    public void BeginRead(Action<string> onOutput, Action<string> onError) {
        outputTask = Task.Run(() => ReadLines(output, onOutput)); errorTask = Task.Run(() => ReadLines(error, onError));
    }
    private static void ReadLines(StreamReader reader, Action<string> handler) {
        try { string line; while ((line = reader.ReadLine()) != null) handler(line); }
        catch (IOException) { /* Parent observation can close pipes while work survives. */ }
        catch (ObjectDisposedException) { }
    }
    public bool WaitForExit(int timeout) {
        int result = WaitForSingleObject(processHandle, timeout);
        if (result == -1) throw new Win32Exception();
        return result == 0;
    }
    public void FinishReading() {
        if (outputTask != null && !Task.WaitAll(new[] { outputTask, errorTask }, 15000)) throw new TimeoutException("Dependency output has not closed yet.");
    }
    public void Dispose() {
        if (processHandle != IntPtr.Zero) { CloseHandle(processHandle); processHandle = IntPtr.Zero; }
        // Disposing a StreamReader during a blocking ReadLine can wait for an
        // orphan child's pipe. Release it after the reader finishes instead.
        DisposeReader(output, outputTask); DisposeReader(error, errorTask);
    }
    private static void DisposeReader(StreamReader reader, Task task) {
        if (task == null || task.IsCompleted) reader.Dispose();
        else task.ContinueWith(completed => reader.Dispose());
    }
}
