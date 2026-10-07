"""Real Windows locks and process exit during partial package rollback."""
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

internal static class LockedRollbackChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static readonly string[] Names = { "first.txt", "introduced.txt", "last.txt" };
    static void CheckPrior(string root) {
        Check(File.ReadAllText(Path.Combine(root, Names[0])) == "prior first", "First file not restored");
        Check(!File.Exists(Path.Combine(root, Names[1])), "New file survived rollback");
        Check(File.ReadAllText(Path.Combine(root, Names[2])) == "prior last", "Last file not restored");
        Check(File.ReadAllText(Path.Combine(root, "user-data.txt")) == "keep user data", "Unlisted data changed");
    }
    static void Main(string[] args) {
        string mode = args[0], root = args[1];
        var options = new InstallerOptions(root, root, "unused.exe", true, null);
        if (mode == "interrupt") {
            int locked = Int32.Parse(args[2]);
            Directory.CreateDirectory(root);
            File.WriteAllText(Path.Combine(root, Names[0]), "prior first");
            File.WriteAllText(Path.Combine(root, Names[2]), "prior last");
            File.WriteAllText(Path.Combine(root, "user-data.txt"), "keep user data");
            var transaction = AppFileTransaction.Begin(root);
            var entries = new AppFileTransaction.Entry[Names.Length];
            for (int i = 0; i < Names.Length; i++) {
                string target = Path.Combine(root, Names[i]);
                string before = File.Exists(target) ? AppFileTransaction.Hash(target) : null;
                if (before != null) File.Copy(target, transaction.BackupPath(i));
                File.WriteAllText(transaction.StagedPath(i), "next " + Names[i]);
                entries[i] = new AppFileTransaction.Entry { path = Names[i], before = before,
                    after = AppFileTransaction.Hash(transaction.StagedPath(i)) };
            }
            transaction.Prepare(entries);
            for (int i = 0; i < Names.Length; i++) {
                string target = Path.Combine(root, Names[i]);
                if (File.Exists(target)) File.Replace(transaction.StagedPath(i), target, null);
                else File.Move(transaction.StagedPath(i), target);
            }
            // Allow hashes to read this file while denying rename/delete. This
            // is a real Windows sharing violation, not a mocked exception.
            using (var held = new FileStream(Path.Combine(root, Names[locked]), FileMode.Open,
                    FileAccess.Read, FileShare.Read)) {
                bool blocked = false;
                using (var operations = new WindowsInstallerOperations(options)) {
                    try { operations.RecoverAppFiles(); }
                    catch (IOException error) {
                        blocked = error.InnerException is AggregateException;
                    }
                }
                Check(blocked, "Locked rollback was not reported as incomplete");
                Check(AppFileTransaction.Pending(root), "Partial rollback discarded its journal");
                for (int i = 0; i < Names.Length; i++) {
                    string target = Path.Combine(root, Names[i]);
                    if (i == locked) {
                        Check(File.ReadAllText(target) == "next " + Names[i], "Locked file changed");
                        if (entries[i].before != null)
                            Check(AppFileTransaction.Hash(transaction.BackupPath(i)) == entries[i].before,
                                "Required recovery copy lost");
                    } else if (entries[i].before == null) {
                        Check(!File.Exists(target), "Unlocked new file was not removed");
                    } else {
                        Check(AppFileTransaction.Hash(target) == entries[i].before,
                            "Unlocked prior file was not restored");
                    }
                }
                // Do not unwind/dispose: Windows releases the lock when this
                // fixture process exits; a different process must then recover.
                Environment.Exit(75);
            }
        } else if (mode == "recover") {
            using (var operations = new WindowsInstallerOperations(options)) operations.RecoverAppFiles();
            CheckPrior(root);
            Check(!AppFileTransaction.Pending(root), "Finished rollback retained its journal");
            string setup = Path.Combine(root, ".bloons-setup");
            Check(Directory.GetFiles(setup, "*.old", SearchOption.AllDirectories).Length == 0,
                "Finished rollback retained old copies");
            Check(Directory.GetFiles(setup, "*.new", SearchOption.AllDirectories).Length == 0,
                "Finished rollback retained staged copies");
            Check(Directory.GetDirectories(setup, "files-*", SearchOption.TopDirectoryOnly).Length == 0,
                "Finished rollback retained its transaction directory");
        } else if (mode == "install") {
            CheckPrior(root);
            string zip = Path.Combine(root, "next.zip");
            using (var stream = new FileStream(zip, FileMode.CreateNew))
            using (var archive = new ZipArchive(stream, ZipArchiveMode.Create))
                foreach (string name in Names)
                    using (var writer = new StreamWriter(archive.CreateEntry(name).Open())) writer.Write("next " + name);
            using (var operations = new WindowsInstallerOperations(options)) operations.InstallAppFiles(zip);
            foreach (string name in Names)
                Check(File.ReadAllText(Path.Combine(root, name)) == "next " + name, "Retry did not install complete package");
            Check(File.ReadAllText(Path.Combine(root, "user-data.txt")) == "keep user data", "Retry changed unlisted data");
            Check(!AppFileTransaction.Pending(root), "Retry did not commit");
        } else throw new Exception("Unknown fixture mode");
    }
}
'''


@unittest.skipUnless(os.name == 'nt', 'Actual Windows file-sharing semantics')
class InstallerLockedRollbackTests(unittest.TestCase):
    def test_partial_locked_rollback_recovers_after_process_exit_and_allows_retry(self):
        with tempfile.TemporaryDirectory(prefix='bloons-rollback-') as folder:
            binary = compile_harness(folder, 'LockedRollbackChecks', HARNESS)
            for locked in range(3):
                with self.subTest(locked_file=locked):
                    root = Path(folder) / ('case-' + str(locked))
                    stopped = subprocess.run([str(binary), 'interrupt', str(root), str(locked)],
                                             capture_output=True, text=True, timeout=30)
                    self.assertEqual(stopped.returncode, 75, stopped.stdout + stopped.stderr)
                    self.assertTrue((root / '.bloons-setup/app-file-transaction.json').is_file())
                    for mode in ('recover', 'recover', 'install'):
                        resumed = subprocess.run([str(binary), mode, str(root)],
                                                 capture_output=True, text=True, timeout=30)
                        self.assertEqual(resumed.returncode, 0, mode + ': ' + resumed.stdout + resumed.stderr)


if __name__ == '__main__':
    unittest.main()
