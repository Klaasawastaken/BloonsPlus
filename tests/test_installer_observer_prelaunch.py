"""Exercise owner interruption between observer readiness and dependency launch."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native job objects')
class InstallerObserverPrelaunchTests(unittest.TestCase):
    def test_ready_observer_waits_for_launch_or_exact_owner_exit(self):
        with tempfile.TemporaryDirectory(prefix='bloons-observer-prelaunch-') as folder:
            binary = compile_harness(folder, 'ObserverPrelaunchChecks', SOURCE)
            run = subprocess.run([str(binary), 'main', folder],
                                 capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result['beforeExit'], 'unknown')
            self.assertTrue(result['blockedBeforeExit'])
            self.assertFalse(result['prematureEmpty'])
            self.assertEqual(result['afterExit'], 'idle')
            self.assertTrue(result['emptyObserved'])
            self.assertFalse(result['terminalClaimed'])
            self.assertFalse(result['exitCodeClaimed'])
            self.assertFalse(result['blockedAfterExit'])


SOURCE = r'''
using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
using System.Runtime.InteropServices;
using System.Web.Script.Serialization;
internal static class ObserverPrelaunchChecks {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateJobObject(IntPtr security, string name);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    static string Self { get { return Process.GetCurrentProcess().MainModule.FileName; } }
    static string Q(string value) { return "\""+value+"\""; }
    static void Check(bool value, string why) { if(!value) throw new Exception(why); }
    static bool LockBlocked(string root) {
        try { using(InstallerEngine.AcquireInstallLock(root)) {} return false; }
        catch(InvalidOperationException) { return true; }
    }
    static void Main(string[] args) {
        if(InstallerProcessObserver.TryRun(args)) return;
        try { Run(args); }
        catch(Exception error) { Console.Error.WriteLine(error); Environment.ExitCode=1; }
    }
    static void Run(string[] args) {
        string root=Path.GetFullPath(args[1]);
        var serializer=new JavaScriptSerializer();
        string receiptFile=Path.Combine(root,".bloons-setup","owned-process.json");
        string readyFile=Path.Combine(root,"owner-ready");
        if(args[0]=="owner") {
            // Reproduce the production prelaunch ordering deterministically,
            // without adding a pause hook to OwnedProcess.Start or launching a
            // dependency: create job, persist intent, handshake, then wait.
            string name="BloonsPlusInstall."+Guid.NewGuid().ToString("N");
            IntPtr job=CreateJobObject(IntPtr.Zero,name);
            Check(job!=IntPtr.Zero,"Fixture job creation failed");
            try {
                InstallSession.AtomicWrite(receiptFile,serializer.Serialize(new OwnedProcess.Receipt {
                    // The real lock reads the real boot identity. A made-up
                    // value would simulate a reboot whenever WMI is available.
                    Executable=Self,Kind="python_dependency",JobName=name,BootIdentity=OwnedProcess.CurrentBootIdentity
                }));
                using(var observer=InstallerProcessObserver.Start(root,name)) {
                    InstallSession.AtomicWrite(readyFile,name);
                    Thread.Sleep(15000);
                }
            } finally { CloseHandle(job); }
            return;
        }
        using(var owner=Process.Start(new ProcessStartInfo(Self,"owner "+Q(root)) {
            UseShellExecute=false,CreateNoWindow=true,WindowStyle=ProcessWindowStyle.Hidden
        })) {
            long ownerStart=owner.StartTime.ToUniversalTime().Ticks;
            string observedJob=null;
            try {
                var wait=Stopwatch.StartNew();
                while(!File.Exists(readyFile)&&wait.ElapsedMilliseconds<12000&&!owner.HasExited)Thread.Sleep(20);
                Check(File.Exists(readyFile),"Observer readiness missing");
                string name=File.ReadAllText(readyFile);
                observedJob=name;
                using(var observation=new OwnedProcess(root)) {
                    // An empty job is insufficient while the owner can still
                    // launch its dependency. Check across observer poll ticks.
                    var beforeWait=Stopwatch.StartNew();
                    while(beforeWait.ElapsedMilliseconds<600) {
                        Check(!InstallerProcessObserver.ObservedEmpty(root,name),"Observer declared empty before launch window closed");
                        Check(observation.Observe()=="unknown","Pending launch became idle before owner exit");
                        Thread.Sleep(30);
                    }
                    string beforeExit=observation.Observe();
                    bool blockedBeforeExit=LockBlocked(root);
                    Check(blockedBeforeExit,"Second installer admitted before pending launch ended");
                    Check(OwnedProcess.Matches(owner.Id,ownerStart,Self),"Exact fixture owner identity changed");
                    owner.Kill(); Check(owner.WaitForExit(5000),"Own fixture owner did not exit");
                    var emptyWait=Stopwatch.StartNew();
                    while(!InstallerProcessObserver.ObservedEmpty(root,name)&&emptyWait.ElapsedMilliseconds<5000)Thread.Sleep(30);
                    bool emptyObserved=InstallerProcessObserver.ObservedEmpty(root,name);
                    string afterExit=observation.Observe();
                    bool blockedAfterExit=LockBlocked(root);
                    var receipt=serializer.Deserialize<OwnedProcess.Receipt>(File.ReadAllText(receiptFile));
                    Console.WriteLine(serializer.Serialize(new {
                        beforeExit,blockedBeforeExit,prematureEmpty=false,afterExit,emptyObserved,
                        terminalClaimed=receipt.TerminalObserved,exitCodeClaimed=receipt.ExitCode.HasValue,blockedAfterExit
                    }));
                }
            } finally {
                // Kill only the process this fixture created, after checking
                // its executable and creation time. The observer exits itself.
                if(OwnedProcess.Matches(owner.Id,ownerStart,Self)) {
                    owner.Kill(); owner.WaitForExit(5000);
                }
                // Release a deliberately broken observer in negative-control
                // runs after collecting the result. Only this fixture's named
                // launch event is signalled; no dependency is ever launched.
                if(observedJob!=null) {
                    try { using(var launched=EventWaitHandle.OpenExisting(observedJob+".Launched")) launched.Set(); }
                    catch(WaitHandleCannotBeOpenedException) {}
                    var cleanupWait=Stopwatch.StartNew();
                    while(!InstallerProcessObserver.ObservedEmpty(root,observedJob)&&cleanupWait.ElapsedMilliseconds<5000)Thread.Sleep(30);
                }
            }
        }
    }
}
'''
