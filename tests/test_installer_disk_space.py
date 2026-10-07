"""Real native deployment with deterministic available-space observations."""
import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness

HARNESS = r'''
using System;
using System.IO;
using System.IO.Compression;
internal sealed class SpaceDeployment : WindowsInstallerOperations {
    readonly long available;
    public int Reads;
    public SpaceDeployment(InstallerOptions options, long bytes) : base(options) { available=bytes; }
    protected override long AvailableInstallBytes() { Reads++; return available; }
}
internal static class DiskSpaceChecks {
    static void Check(bool value, string why) { if(!value) throw new Exception(why); }
    static void Main(string[] args) {
        string root=args[0], mode=args[1], zip=Path.Combine(root,"package.zip");
        Directory.CreateDirectory(root);
        byte[] old=new byte[1024*1024], next=new byte[200];
        File.WriteAllBytes(Path.Combine(root,"existing.bin"),old);
        File.WriteAllText(Path.Combine(root,"user-data.txt"),"untouched");
        using(var stream=File.Create(zip)) using(var archive=new ZipArchive(stream,ZipArchiveMode.Create)) {
            using(var entry=archive.CreateEntry("existing.bin").Open()) {
                byte[] content=mode=="unchanged" ? old : next;
                entry.Write(content,0,content.Length);
            }
            if(mode!="unchanged") using(var entry=archive.CreateEntry("new.bin").Open()) entry.Write(next,0,next.Length);
        }
        long reserve=16L*1024*1024;
        long required=reserve+old.Length+next.Length*2;
        long available=mode=="enough" ? required : mode=="unchanged" ? reserve : required-1;
        var options=new InstallerOptions(root,root,"unused.exe",true,null);
        using(var operations=new SpaceDeployment(options,available)) {
            bool refused=false;
            try { operations.InstallAppFiles(zip); }
            catch(IOException error) { refused=error.Message.Contains("free disk space"); if(!refused) throw; }
            Check(operations.Reads==1,"Deployment did not observe capacity exactly once");
            Check(refused==(mode=="short"),"Wrong capacity decision");
        }
        Check(File.ReadAllText(Path.Combine(root,"user-data.txt"))=="untouched","Unlisted data changed");
        if(mode=="short") {
            Check(new FileInfo(Path.Combine(root,"existing.bin")).Length==old.Length,"Original was replaced before capacity check");
            Check(!File.Exists(Path.Combine(root,"new.bin")),"New file applied before capacity check");
            Check(!Directory.Exists(Path.Combine(root,".bloons-setup")),"Capacity refusal created transaction state");
        } else {
            Check(new FileInfo(Path.Combine(root,"existing.bin")).Length==(mode=="unchanged" ? old.Length : next.Length),"Wrong installed content");
            Check(!AppFileTransaction.Pending(root),"Deployment left pending transaction");
        }
    }
}
'''

@unittest.skipUnless(os.name == 'nt', 'Windows native installer')
class InstallerDiskSpaceTests(unittest.TestCase):
    def test_capacity_before_staging_includes_backups_and_reuses_unchanged_files(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory(prefix='bloons-space-') as folder:
            binary=compile_harness(folder,'DiskSpaceChecks',HARNESS)
            for mode in ('short','enough','unchanged'):
                with self.subTest(mode=mode):
                    run=subprocess.run([str(binary),str(Path(folder)/mode),mode],capture_output=True,text=True,timeout=30)
                    self.assertEqual(run.returncode,0,run.stdout+run.stderr)
