"""Fresh-process recovery after exits inside real native package deployment."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness

HARNESS = r'''
using System;
using System.IO;
using System.IO.Compression;

internal sealed class ExitingDeployment : WindowsInstallerOperations {
    private readonly bool exitAfterCommit;
    public ExitingDeployment(InstallerOptions options, string point) : base(options) {
        exitAfterCommit = point == "committed-first";
        ProgressChanged += progress => {
            if (progress.Stage != InstallerStage.Files || !progress.Numerator.HasValue || progress.Numerator.Value <= 0) return;
            if ((point == "staged-first" && progress.Message.StartsWith("Preparing Bloons+ files"))
                || (point == "prepared" && progress.Message.StartsWith("Applying verified")))
                Environment.Exit(75); // Exit before finally/rollback handlers can unwind.
        };
    }
    protected override void CommitStagedFile(string staged, string destination) {
        base.CommitStagedFile(staged, destination);
        if (exitAfterCommit) Environment.Exit(75);
    }
}
internal static class DeploymentExitChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static readonly string[] Names = { "existing.txt", "introduced.txt", "last.txt" };
    static void Prior(string root) {
        Check(File.ReadAllText(Path.Combine(root, Names[0])) == "prior first", "Original first file lost");
        Check(!File.Exists(Path.Combine(root, Names[1])), "Uncommitted new file installed");
        Check(File.ReadAllText(Path.Combine(root, Names[2])) == "prior last", "Original last file lost");
        Check(File.ReadAllText(Path.Combine(root, "user-data.txt")) == "untouched", "Unlisted data changed");
    }
    static void Main(string[] args) {
        string mode=args[0], root=args[1], zip=Path.Combine(root,"package.zip");
        var options=new InstallerOptions(root, root, "unused.exe", true, null);
        if (mode == "interrupt") {
            Directory.CreateDirectory(root);
            File.WriteAllText(Path.Combine(root, Names[0]), "prior first");
            File.WriteAllText(Path.Combine(root, Names[2]), "prior last");
            File.WriteAllText(Path.Combine(root, "user-data.txt"), "untouched");
            using (var output=new FileStream(zip,FileMode.CreateNew))
            using (var archive=new ZipArchive(output,ZipArchiveMode.Create))
                foreach(string name in Names)
                    using(var writer=new StreamWriter(archive.CreateEntry(name).Open())) writer.Write("next "+name);
            using(var operations=new ExitingDeployment(options,args[2])) operations.InstallAppFiles(zip);
            throw new Exception("Requested interruption boundary was never reached");
        }
        if (mode == "recover") {
            using(var operations=new WindowsInstallerOperations(options)) operations.RecoverAppFiles();
            Prior(root);
            Check(!AppFileTransaction.Pending(root),"Recovery retained journal");
            Check(Directory.GetDirectories(Path.Combine(root,".bloons-setup"),"files-*").Length==0,"Recovery retained staging/backup directory");
        } else if (mode == "retry") {
            Prior(root);
            using(var operations=new WindowsInstallerOperations(options)) operations.InstallAppFiles(zip);
            foreach(string name in Names) Check(File.ReadAllText(Path.Combine(root,name))=="next "+name,"Retry missed a package file");
            Check(File.ReadAllText(Path.Combine(root,"user-data.txt"))=="untouched","Retry changed unlisted data");
            Check(!AppFileTransaction.Pending(root),"Retry did not commit");
            Check(Directory.GetDirectories(Path.Combine(root,".bloons-setup"),"files-*").Length==0,"Retry retained staging/backup directory");
        } else throw new Exception("Unknown mode");
    }
}
'''

@unittest.skipUnless(os.name == 'nt', 'Actual Windows native deployment')
class InstallerDeploymentExitTests(unittest.TestCase):
    def test_real_deployment_exit_recovers_in_new_process_and_retries(self):
        import json
        with tempfile.TemporaryDirectory(prefix='bloons-deploy-exit-') as folder:
            binary=compile_harness(folder,'DeploymentExitChecks',HARNESS)
            for point in ('staged-first','prepared','committed-first'):
                with self.subTest(point=point):
                    root=Path(folder)/point
                    run=subprocess.run([str(binary),'interrupt',str(root),point],capture_output=True,text=True,timeout=30)
                    self.assertEqual(run.returncode,75,run.stdout+run.stderr)
                    journal=json.loads((root/'.bloons-setup/app-file-transaction.json').read_text(encoding='utf-8-sig'))
                    self.assertEqual(journal['phase'],'preparing' if point=='staged-first' else 'prepared')
                    self.assertEqual((root/'existing.txt').read_text(),'next existing.txt' if point=='committed-first' else 'prior first')
                    self.assertFalse((root/'introduced.txt').exists())
                    self.assertEqual((root/'last.txt').read_text(),'prior last')
                    self.assertTrue(list((root/'.bloons-setup').glob('files-*/*.old')))
                    for mode in ('recover','recover','retry'):
                        run=subprocess.run([str(binary),mode,str(root)],capture_output=True,text=True,timeout=30)
                        self.assertEqual(run.returncode,0,mode+': '+run.stdout+run.stderr)

if __name__ == '__main__':
    unittest.main()
