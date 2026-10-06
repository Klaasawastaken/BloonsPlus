import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerArchiveTests(unittest.TestCase):
    def test_locked_replacement_keeps_prior_file_and_cleans_staging(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'ArchiveChecks', r'''
using System;
using System.IO;
using System.IO.Compression;
internal sealed class InterruptedCommit : WindowsInstallerOperations {
    public bool Staged;
    public InterruptedCommit(InstallerOptions options) : base(options) {}
    protected override void CommitStagedFile(string staged, string destination) {
        Staged = File.ReadAllText(staged) == "new data";
        throw new IOException("Interrupted before replacement");
    }
}
internal static class ArchiveChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main() {
        string root = Path.Combine(Path.GetTempPath(), "Bloons-archive-" + Guid.NewGuid().ToString("N"));
        try {
            Directory.CreateDirectory(root); string destination = Path.Combine(root, "existing.txt");
            File.WriteAllText(destination, "prior data"); string zip = Path.Combine(root, "package.zip");
            using (var output = new FileStream(zip, FileMode.Create))
            using (var archive = new ZipArchive(output, ZipArchiveMode.Create))
            using (var writer = new StreamWriter(archive.CreateEntry("existing.txt").Open())) writer.Write("new data");
            var options = new InstallerOptions(root, root, "unused.exe", true, null);
            var operations = new WindowsInstallerOperations(options);
            InstallerProgress copied = null;
            operations.ProgressChanged += progress => { if (progress.Stage == InstallerStage.Files && progress.Percent == 100) copied = progress; };
            var interrupted = new InterruptedCommit(options);
            try { interrupted.InstallAppFiles(zip); throw new Exception("Injected interruption ignored"); }
            catch (IOException) {}
            Check(interrupted.Staged, "Replacement was not staged before commit");
            Check(File.ReadAllText(destination) == "prior data", "Interruption damaged prior data");
            Check(Directory.GetFiles(root, "*.tmp").Length == 0, "Interrupted staging remains");
            using (var held = new FileStream(destination, FileMode.Open, FileAccess.Read, FileShare.Read)) {
                try { operations.InstallAppFiles(zip); throw new Exception("Locked file replacement accepted"); }
                catch (IOException) {}
                Check(Directory.GetFiles(root, "*.tmp").Length == 0, "Staging remains after failure");
            }
            Check(File.ReadAllText(destination) == "prior data", "Failed replacement damaged prior data");
            operations.InstallAppFiles(zip);
            Check(File.ReadAllText(destination) == "new data", "Replacement did not finish");
            Check(copied != null && copied.Numerator == new FileInfo(destination).Length && copied.Denominator == copied.Numerator,
                "Actual copied byte counts lost");
            DateTime modified = File.GetLastWriteTimeUtc(destination);
            operations.InstallAppFiles(zip);
            Check(File.GetLastWriteTimeUtc(destination) == modified, "Unchanged file rewritten");
        } finally { if (Directory.Exists(root)) Directory.Delete(root, true); }
    }
}
''')
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
