"""Observe the exact native job launch across a fixture-only parent interruption."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native job objects')
class InstallerProcessTreeInterruptionTests(unittest.TestCase):
    def test_lost_observer_retains_unknown_instead_of_releasing_work(self):
        with tempfile.TemporaryDirectory(prefix='bloons-native-observer-') as folder:
            root = Path(folder)
            binary = compile_harness(root, 'NativeTreeAcceptance', SOURCE)
            run = subprocess.run([str(binary), 'main', str(root / 'fixture'), 'lose-observer'],
                                 capture_output=True, text=True, timeout=40)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads(run.stdout)
            self.assertTrue(result['blockedAfterParent'])
            self.assertTrue(result['leafSurvived'])
            self.assertEqual(result['afterLeaf'], 'unknown')
            self.assertTrue(result['blockedAfterLeaf'])

    def test_surviving_descendant_blocks_second_installer(self):
        with tempfile.TemporaryDirectory(prefix='bloons-native-tree-') as folder:
            root = Path(folder)
            binary = compile_harness(root, 'NativeTreeAcceptance', SOURCE)
            run = subprocess.run([str(binary), 'main', str(root / 'fixture')],
                                 capture_output=True, text=True, timeout=40)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result['beforeInterruption'], 'running')
            self.assertTrue(result['terminalRejected'])
            self.assertNotEqual(result['afterParent'], 'idle')
            self.assertTrue(result['blockedAfterParent'])
            self.assertTrue(result['leafSurvived'])
            self.assertTrue(result['leafNaturalExit'])
            # A surviving observer must retain the job through the owner's exit
            # and durably prove it empty before another installer can recover.
            self.assertEqual(result['afterLeaf'], 'idle')
            self.assertFalse(result['blockedAfterLeaf'])


SOURCE = r'''

using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
using System.Web.Script.Serialization;
using System.Collections.Generic;
internal static class NativeTreeAcceptance {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static string Self { get { return Process.GetCurrentProcess().MainModule.FileName; } }
    static string Q(string value) { return "\"" + value + "\""; }
    static bool LockBlocked(string root) {
        try { using (InstallerEngine.AcquireInstallLock(root)) {} return false; }
        catch (InvalidOperationException) { return true; }
    }
    static void Main(string[] args) {
        if (InstallerProcessObserver.TryRun(args)) return;
        try { Run(args); }
        catch(Exception error) { Console.Error.WriteLine(error.ToString()); Environment.ExitCode=1; }
    }
    static void Run(string[] args) {
        string role = args[0], root = Path.GetFullPath(args[1]);
        Directory.CreateDirectory(root);
        if (role == "leaf") {
            Thread.Sleep(12000);
            File.WriteAllText(Path.Combine(root, "leaf-done"), "natural exit");
            return;
        }
        if (role == "intermediate") {
            using (var leaf = Process.Start(new ProcessStartInfo(Self, "leaf " + Q(root)) {UseShellExecute=false,CreateNoWindow=true})) {
                File.WriteAllText(Path.Combine(root,"leaf.pid"), leaf.Id.ToString());
            }
            return;
        }
        if (role == "worker") {
            var existing=new HashSet<int>();
            foreach(var process in Process.GetProcessesByName(Path.GetFileNameWithoutExtension(Self)))
                using(process)existing.Add(process.Id);
            using (var owner = new OwnedProcess(root))
            using (var child = owner.Start(Self,"intermediate " + Q(root),root)) {
                child.BeginRead(line=>{},line=>{});
                Check(child.WaitForExit(5000),"Intermediate did not exit");
                if(args.Length>2&&args[2]=="lose-observer") {
                    int leafId=Int32.Parse(File.ReadAllText(Path.Combine(root,"leaf.pid")));
                    var candidates=new List<Process>();
                    foreach(var process in Process.GetProcessesByName(Path.GetFileNameWithoutExtension(Self))) {
                        if(!existing.Contains(process.Id)&&process.Id!=leafId&&process.Id!=child.Id
                            &&String.Equals(process.MainModule.FileName,Self,StringComparison.OrdinalIgnoreCase))candidates.Add(process);
                        else process.Dispose();
                    }
                    Check(candidates.Count==1,"Could not identify exact fixture observer");
                    using(var lost=candidates[0]){lost.Kill();Check(lost.WaitForExit(5000),"Own observer did not exit");}
                }
                bool terminalRejected = false;
                try { owner.RecordTerminal(child.ExitCode); }
                catch (InvalidOperationException) { terminalRejected = true; }
                File.WriteAllText(Path.Combine(root,"worker-ready.json"),new JavaScriptSerializer().Serialize(new {
                    terminalRejected, observation=owner.Observe(), blocked=LockBlocked(root)
                }));
                Thread.Sleep(25000);
            }
            return;
        }
        Process worker=null, leafProcess=null;
        object result=null;
        try {
            Directory.CreateDirectory(root);
            worker=Process.Start(new ProcessStartInfo(Self,"worker "+Q(root)+(args.Length>2?" "+args[2]:"")) {UseShellExecute=false,CreateNoWindow=true});
            var ready=Path.Combine(root,"worker-ready.json");
            var wait=Stopwatch.StartNew();
            while(!File.Exists(ready)&&wait.ElapsedMilliseconds<8000&&!worker.HasExited)Thread.Sleep(20);
            Check(File.Exists(ready),"Worker readiness missing");
            var initial=new JavaScriptSerializer().Deserialize<dynamic>(File.ReadAllText(ready));
            Check((bool)initial["terminalRejected"],"Direct-parent exit falsely completed surviving descendant");
            Check((string)initial["observation"]=="running", "Owned descendant not observed before parent interruption");
            Check((bool)initial["blocked"],"Install lock admitted surviving descendant");
            leafProcess=Process.GetProcessById(Int32.Parse(File.ReadAllText(Path.Combine(root,"leaf.pid"))));
            Check(String.Equals(leafProcess.MainModule.FileName,Self,StringComparison.OrdinalIgnoreCase),"Leaf identity mismatch");
            long leafStart=leafProcess.StartTime.ToUniversalTime().Ticks;
            long workerStart=worker.StartTime.ToUniversalTime().Ticks;
            Check(OwnedProcess.Matches(worker.Id,workerStart,Self),"Worker identity mismatch before interruption");
            worker.Kill();Check(worker.WaitForExit(5000),"Own worker did not terminate");
            using(var observer=new OwnedProcess(root)) {
                string afterParent=observer.Observe();
                bool blockedAfterParent=LockBlocked(root);
                Check(afterParent!="idle"&&blockedAfterParent,"Parent interruption admitted a second installer");
                Check(OwnedProcess.Matches(leafProcess.Id,leafStart,Self),"Leaf unexpectedly terminated with parent");
                Check(leafProcess.WaitForExit(16000),"Own leaf did not finish naturally");
                Check(File.Exists(Path.Combine(root,"leaf-done")),"Natural terminal marker absent");
                var terminalWait=Stopwatch.StartNew();
                while(observer.Observe()!="idle"&&terminalWait.ElapsedMilliseconds<3000)Thread.Sleep(50);
                string afterLeaf=observer.Observe();
                bool blockedAfterLeaf=LockBlocked(root);
                result=new {beforeInterruption=(string)initial["observation"],terminalRejected=(bool)initial["terminalRejected"],afterParent,blockedAfterParent,leafSurvived=true,leafNaturalExit=true,afterLeaf,blockedAfterLeaf,realBootAvailable=!String.IsNullOrEmpty(OwnedProcess.CurrentBootIdentity)};
            }
        } finally {
            foreach(var process in new[]{worker,leafProcess})if(process!=null){
                try { if(!process.HasExited&&String.Equals(process.MainModule.FileName,Self,StringComparison.OrdinalIgnoreCase)){process.Kill();process.WaitForExit(5000);} } catch {}
                process.Dispose();
            }
            // Empty-job evidence can be written just before the observer's final
            // process exit. Wait for this unique fixture executable to release
            // its file before TemporaryDirectory tries to remove it.
            foreach(var process in Process.GetProcessesByName(Path.GetFileNameWithoutExtension(Self)))using(process){
                if(process.Id==Process.GetCurrentProcess().Id)continue;
                try {
                    if(!process.HasExited&&String.Equals(process.MainModule.FileName,Self,StringComparison.OrdinalIgnoreCase))
                        Check(process.WaitForExit(5000),"Own fixture observer did not exit after its work ended");
                } catch(InvalidOperationException) { if(!process.HasExited)throw; }
                  catch(System.ComponentModel.Win32Exception) { if(!process.HasExited)throw; }
            }
        }
        Console.WriteLine(new JavaScriptSerializer().Serialize(result));
    }
}
'''
