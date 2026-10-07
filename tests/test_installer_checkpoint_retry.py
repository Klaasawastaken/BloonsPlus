"""Bounded checkpoint replacement retries without deleting the prior receipt."""
import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness

HARNESS = r'''
using System;
using System.IO;
using System.Collections.Generic;
using System.Threading;
internal sealed class NativeWriteError : IOException {
    public NativeWriteError(int code) { HResult=unchecked((int)0x80070000)|code; }
}
internal static class CheckpointRetryChecks {
    static void Check(bool ok,string why) { if(!ok) throw new Exception(why); }
    static void Main(string[] args) {
        string root=args[0]; Directory.CreateDirectory(root);
        foreach(int code in new[]{32,33,1175,5,1176,1177}) foreach(bool persistent in new[]{false,true}) {
            string prior=Path.Combine(root,"session.json"), next=prior+".next";
            File.WriteAllText(prior,"prior");File.WriteAllText(next,"next");
            int calls=0;var waits=new List<int>();bool failed=false;
            bool transient=code==32||code==33||code==1175;
            try {
                InstallSession.ReplaceCheckpoint(next,prior,(source,destination)=>{
                    calls++;Check(File.ReadAllText(destination)=="prior","Prior receipt changed during retry");
                    if(persistent||calls==1) throw new NativeWriteError(code);
                    File.Replace(source,destination,null);
                },ms=>waits.Add(ms));
            } catch(NativeWriteError e) { failed=true;Check((e.HResult&65535)==code,"Original error lost"); }
            Check(failed==(!transient||persistent),"Wrong retry outcome for "+code);
            Check(calls==(transient?(persistent?4:2):1),"Wrong bounded attempt count for "+code);
            Check(String.Join(",",waits)==(transient?(persistent?"50,100,200":"50"):""),"Wrong backoff");
            Check(File.ReadAllText(prior)==(failed?"prior":"next"),"Wrong final receipt");
            if(File.Exists(next))File.Delete(next);
        }
        // A disappearing source cannot be repaired by repeating replacement.
        string old=Path.Combine(root,"missing.json"),temp=old+".next";
        File.WriteAllText(old,"prior");File.WriteAllText(temp,"next");int attempts=0;
        try { InstallSession.ReplaceCheckpoint(temp,old,(a,b)=>{attempts++;File.Delete(a);throw new NativeWriteError(1175);},ms=>{throw new Exception("Retried missing source");}); }
        catch(NativeWriteError) { }
        Check(attempts==1&&File.ReadAllText(old)=="prior","Missing-source failure changed prior receipt");
        InstallSession.AtomicWrite(old,"actual write");
        Check(File.ReadAllText(old)=="actual write","Real atomic writer did not publish");
        using(var ready=new ManualResetEvent(false)) {
            var holder=new Thread(()=>{using(var handle=new FileStream(old,FileMode.Open,FileAccess.Read,FileShare.Read)){ready.Set();Thread.Sleep(120);}});
            holder.Start();Check(ready.WaitOne(5000),"Lock holder did not start");
            try { InstallSession.AtomicWrite(old,"after transient lock"); } finally { holder.Join(); }
        }
        Check(File.ReadAllText(old)=="after transient lock","Real writer did not recover from sharing conflict");
        using(var handle=new FileStream(old,FileMode.Open,FileAccess.Read,FileShare.Read)) {
            bool rejected=false;try{InstallSession.AtomicWrite(old,"must not publish");}catch(IOException){rejected=true;}
            Check(rejected,"Persistent lock was not reported");
        }
        Check(File.ReadAllText(old)=="after transient lock","Persistent lock lost the valid receipt");
        Check(Directory.GetFiles(root,"*.tmp").Length==0,"Atomic writer retained incomplete temporary files");
    }
}
'''

@unittest.skipUnless(os.name == 'nt', 'Windows native installer')
class InstallerCheckpointRetryTests(unittest.TestCase):
    def test_transient_replacement_errors_are_bounded_and_preserve_prior_receipt(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory(prefix='bloons-checkpoint-') as folder:
            binary=compile_harness(folder,'CheckpointRetryChecks',HARNESS)
            run=subprocess.run([str(binary),str(Path(folder)/'data')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
