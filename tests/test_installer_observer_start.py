"""No dependency launch without a retained observer; old evidence is scoped."""
import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native job objects')
class InstallerObserverStartTests(unittest.TestCase):
    def test_missing_observer_handshake_prevents_dependency_launch(self):
        with tempfile.TemporaryDirectory(prefix='bloons-observer-start-') as folder:
            binary = compile_harness(folder, 'ObserverStartChecks', r'''
using System;
using System.IO;
using System.Diagnostics;
using System.Web.Script.Serialization;
internal static class ObserverStartChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main(string[] args) {
        if(args.Length>0 && args[0]=="/observe-dependency") { Environment.ExitCode=1; return; }
        if(args.Length>0 && args[0]=="dependency") { File.WriteAllText(args[1],"started"); return; }
        string root=args[0], self=Process.GetCurrentProcess().MainModule.FileName;
        string marker=Path.Combine(root,"dependency-started");
        using(var owner=new OwnedProcess(root,()=>"fixture-boot")) {
            bool rejected=false;
            try { using(var child=owner.Start(self,"dependency \""+marker+"\"",root)) {} }
            catch(InvalidOperationException) { rejected=true; }
            Check(rejected,"Dependency launched without observer readiness");
            Check(!File.Exists(marker),"Dependency executed before handshake");
            Check(owner.Observe()=="idle","Known failed launch did not release empty job");
        }
        string first="BloonsPlusInstall."+Guid.NewGuid().ToString("N");
        string second="BloonsPlusInstall."+Guid.NewGuid().ToString("N");
        string observations=Path.Combine(root,".bloons-setup","process-observations");
        Directory.CreateDirectory(observations);
        string json=new JavaScriptSerializer().Serialize(new InstallerProcessObserver.EmptyObservation {JobName=first,EmptyObserved=true});
        File.WriteAllText(Path.Combine(observations,first+".json"),json);
        File.WriteAllText(Path.Combine(observations,second+".json"),json);
        Check(InstallerProcessObserver.ObservedEmpty(root,first),"Exact completed-job evidence was lost");
        Check(!InstallerProcessObserver.ObservedEmpty(root,second),"Old-job evidence released a different operation");
        Check(!InstallerProcessObserver.ObservedEmpty(root,"../outside"),"Invalid job identity accepted");
        Check(InstallerProcessObserver.TryRun(new[]{"/observe-dependency","invalid"}),"Observer mode fell through to installer UI");
        Check(Environment.ExitCode==1,"Malformed observer invocation claimed success");
        Environment.ExitCode=0;
    }
}
''')
            run = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=20)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
