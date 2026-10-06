import os
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerFileTransactionTests(unittest.TestCase):
    def test_linked_destination_is_rejected_for_install_and_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'app'
            outside = Path(folder) / 'outside'
            root.mkdir()
            outside.mkdir()
            target = outside / 'app.txt'
            target.write_text('next')
            linked = root / 'resources'
            created = subprocess.run(['cmd', '/c', 'mklink', '/J', str(linked), str(outside)],
                                     capture_output=True, text=True, timeout=30)
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            setup = root / '.bloons-setup'
            setup.mkdir()
            transaction_id = 'a' * 32
            work = setup / ('files-' + transaction_id)
            work.mkdir()
            (work / '0.old').write_text('prior')

            def digest(text):
                return '-'.join(f'{byte:02X}' for byte in hashlib.sha256(text.encode()).digest())

            (setup / 'app-file-transaction.json').write_text(json.dumps({
                'version': 1, 'id': transaction_id, 'phase': 'prepared',
                'files': [{'path': 'resources/app.txt', 'before': digest('prior'), 'after': digest('next')}]
            }))
            binary = compile_harness(folder, 'LinkedRecoveryChecks', r'''
using System;
using System.IO;
internal static class LinkedRecoveryChecks {
    static void Main(string[] args) {
        bool refused = false;
        try { AppFileTransaction.Destination(args[0], "resources/app.txt"); } catch (InvalidDataException) { refused = true; }
        if (!refused) throw new Exception("Install path crossed a junction");
        refused = false;
        try { AppFileTransaction.Recover(args[0]); } catch (InvalidDataException) { refused = true; }
        if (!refused) throw new Exception("Recovery path crossed a junction");
    }
}
''')
            run = subprocess.run([str(binary), str(root)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(target.read_text(), 'next')
            self.assertEqual((work / '0.old').read_text(), 'prior')
            self.assertTrue((setup / 'app-file-transaction.json').is_file())

    def test_preparing_exit_and_committed_cleanup_failure_recover_the_correct_version(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'RecoveryPhaseChecks', r'''
using System;
using System.IO;
using System.IO.Compression;
internal sealed class LockedCleanup : WindowsInstallerOperations {
    private FileStream held;
    public LockedCleanup(InstallerOptions options) : base(options) {}
    protected override void CommitStagedFile(string staged, string destination) {
        base.CommitStagedFile(staged, destination);
        held = new FileStream(Path.ChangeExtension(staged, ".old"), FileMode.Open, FileAccess.Read, FileShare.Read);
    }
}
internal static class RecoveryPhaseChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main(string[] args) {
        string root = args[1];
        var options = new InstallerOptions(root, root, "unused.exe", true, null);
        if (args[0] == "preparing" || args[0] == "committed") {
            Directory.CreateDirectory(root); File.WriteAllText(Path.Combine(root, "app.txt"), "prior");
            string zip = Path.Combine(root, "package.zip");
            using (var output = new FileStream(zip, FileMode.CreateNew))
            using (var archive = new ZipArchive(output, ZipArchiveMode.Create))
            using (var writer = new StreamWriter(archive.CreateEntry("app.txt").Open())) writer.Write("next");
            using (var operations = args[0] == "committed" ? new LockedCleanup(options) : new WindowsInstallerOperations(options)) {
                if (args[0] == "preparing") operations.ProgressChanged += progress => {
                    if (progress.Numerator > 0) Environment.Exit(75);
                };
                try { operations.InstallAppFiles(zip); } catch (IOException) {
                    Check(args[0] == "committed", "Unexpected staging failure");
                    string journal = File.ReadAllText(Path.Combine(root, ".bloons-setup", "app-file-transaction.json"));
                    Check(journal.Contains("committed"), "Commit marker was not durable before cleanup");
                    Environment.Exit(75);
                }
            }
            throw new Exception("Interruption was not reached");
        }
        using (var operations = new WindowsInstallerOperations(options)) operations.RecoverAppFiles();
        Check(File.ReadAllText(Path.Combine(root, "app.txt")) == args[2], "Recovery chose the wrong package version");
        Check(!AppFileTransaction.Pending(root), "Recovery left a journal");
        Check(Directory.GetFiles(Path.Combine(root, ".bloons-setup"), "*.old", SearchOption.AllDirectories).Length == 0, "Recovery left old copies");
        Check(Directory.GetFiles(Path.Combine(root, ".bloons-setup"), "*.new", SearchOption.AllDirectories).Length == 0, "Recovery left staged files");
    }
}
''')
            for phase, expected in [('preparing', 'prior'), ('committed', 'next')]:
                root = Path(folder) / phase
                crash = subprocess.run([str(binary), phase, str(root)], capture_output=True, text=True, timeout=30)
                self.assertEqual(crash.returncode, 75, crash.stdout + crash.stderr)
                for _ in range(2):
                    retry = subprocess.run([str(binary), 'recover', str(root), expected], capture_output=True, text=True, timeout=30)
                    self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)

    def test_recovery_rejects_unsafe_journals_before_mutating_app_files(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'UnsafeRecoveryChecks', r'''
using System;
using System.IO;
using System.Web.Script.Serialization;
internal static class UnsafeRecoveryChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main(string[] args) {
        foreach (string scenario in new[] { "traversal", "reserved", "hash", "duplicate", "parent", "unknown-artifact", "oversize" }) {
            string root = Path.Combine(args[0], scenario); Directory.CreateDirectory(root);
            string target = Path.Combine(root, "first.txt"); File.WriteAllText(target, "prior");
            var transaction = AppFileTransaction.Begin(root);
            File.WriteAllText(transaction.StagedPath(0), "next");
            File.Copy(target, transaction.BackupPath(0));
            string before = AppFileTransaction.Hash(target), after = AppFileTransaction.Hash(transaction.StagedPath(0));
            transaction.Prepare(new[] { new AppFileTransaction.Entry { path = "first.txt", before = before, after = after } });
            File.Replace(transaction.StagedPath(0), target, null);
            string journalPath = Path.Combine(root, ".bloons-setup", "app-file-transaction.json");
            var serializer = new JavaScriptSerializer();
            dynamic journal = serializer.DeserializeObject(File.ReadAllText(journalPath));
            if (scenario == "traversal") journal["files"][0]["path"] = "../outside.txt";
            if (scenario == "reserved") journal["files"][0]["path"] = ".bloons-setup/setup-session.json";
            if (scenario == "hash") journal["files"][0]["before"] = "bad hash";
            if (scenario == "duplicate" || scenario == "parent") journal["files"] = new object[] {
                new { path = scenario == "parent" ? "first.txt/child.txt" : "FIRST.txt", before = (string)null, after = after },
                new { path = "first.txt", before = before, after = after }
            };
            string unknown = Path.Combine(Path.GetDirectoryName(transaction.BackupPath(0)), "55.old");
            if (scenario == "unknown-artifact") File.WriteAllText(unknown, "preserve unknown work");
            File.WriteAllText(journalPath, scenario == "oversize" ? new string(' ', 8 * 1024 * 1024 + 1) : serializer.Serialize(journal));
            bool refused = false;
            try { AppFileTransaction.Recover(root); } catch (IOException) { refused = true; } catch (InvalidDataException) { refused = true; }
            Check(refused, scenario + ": unsafe recovery was accepted");
            Check(File.ReadAllText(target) == "next", scenario + ": unsafe journal changed the app before rejection");
            Check(File.ReadAllText(transaction.BackupPath(0)) == "prior", scenario + ": recovery backup lost");
            Check(File.Exists(journalPath), scenario + ": unresolved journal removed");
            if (scenario == "unknown-artifact") Check(File.ReadAllText(unknown) == "preserve unknown work", "Unknown recovery file was deleted");
        }
    }
}
''')
            run = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_pending_recovery_blocks_launch_inventory_and_uninstall(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'PendingRecoveryChecks', r'''
using System;
using System.IO;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
internal static class PendingRecoveryChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main(string[] args) {
        string root = args[0];
        File.WriteAllText(Path.Combine(root, "Bloons+.exe"), "owned app");
        string hash;
        using (var sha = SHA256.Create()) hash = BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(Path.Combine(root, "Bloons+.exe")))).Replace("-", "").ToLowerInvariant();
        File.WriteAllText(Path.Combine(root, "bloons-package.json"), new JavaScriptSerializer().Serialize(new {
            protocolVersion = 1, version = "fixture", fingerprint = "fixture",
            files = new[] { new { path = "Bloons+.exe", sha256 = hash } }
        }));
        Directory.CreateDirectory(Path.Combine(root, ".bloons-setup"));
        File.WriteAllText(Path.Combine(root, ".bloons-setup", "app-file-transaction.json"), "unfinished or damaged journal");
        Check(!InstallerInventory.Inspect(root, "fixture").FilesHealthy, "Pending file recovery was reported healthy");
        bool refused = false;
        try { InstallerInventory.RemoveUnchangedFiles(root); } catch (IOException) { refused = true; }
        Check(refused && File.Exists(Path.Combine(root, "Bloons+.exe")), "Uninstall deleted app before recovery");
        using (var operations = new WindowsInstallerOperations(new InstallerOptions(root, root, "unused.exe", true, null))) {
            refused = false;
            try { operations.LaunchApp(); } catch (IOException error) { refused = error.Message.Contains("recovery"); }
            Check(refused, "Launch did not explain pending app-file recovery");
            Check(!operations.ProbeInstalledRuntime(), "Pending app-file recovery passed runtime readiness");
        }
    }
}
''')
            run = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_retry_restores_package_after_process_exits_between_replacements(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'CrashTransactionChecks', r'''
using System;
using System.IO;
using System.IO.Compression;
internal sealed class CrashAfterReplacement : WindowsInstallerOperations {
    private int count;
    private readonly int crashAt;
    public CrashAfterReplacement(InstallerOptions options, int crashAt) : base(options) { this.crashAt = crashAt; }
    protected override void CommitStagedFile(string staged, string destination) {
        base.CommitStagedFile(staged, destination);
        if (++count == crashAt) Environment.Exit(75);
    }
}
internal static class CrashTransactionChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main(string[] args) {
        string root = args[1];
        var options = new InstallerOptions(root, root, "unused.exe", true, null);
        string zip = Path.Combine(root, "package.zip");
        if (args[0] == "crash") {
            Directory.CreateDirectory(root);
            File.WriteAllText(Path.Combine(root, "first.txt"), "prior first");
            File.WriteAllText(Path.Combine(root, "last.txt"), "prior last");
            using (var output = new FileStream(zip, FileMode.CreateNew))
            using (var archive = new ZipArchive(output, ZipArchiveMode.Create)) {
                foreach (string name in new[] { "first.txt", "introduced.txt", "last.txt" })
                    using (var writer = new StreamWriter(archive.CreateEntry(name).Open())) writer.Write("new " + name);
            }
            using (var operations = new CrashAfterReplacement(options, Int32.Parse(args[2]))) operations.InstallAppFiles(zip);
            throw new Exception("Crash was not reached");
        }
        // Recovery must happen before reading the next package, even if that
        // package is invalid. This uses the actual public installation entry.
        File.WriteAllText(zip, "not a zip");
        using (var operations = new WindowsInstallerOperations(options)) {
            try { operations.InstallAppFiles(zip); throw new Exception("Bad package accepted"); }
            catch (InvalidDataException) {}
        }
        Check(File.ReadAllText(Path.Combine(root, "first.txt")) == "prior first", "Interrupted first replacement was not recovered");
        Check(File.ReadAllText(Path.Combine(root, "last.txt")) == "prior last", "Interrupted last replacement was not recovered");
        Check(!File.Exists(Path.Combine(root, "introduced.txt")), "Interrupted new file remained installed");
        Check(!File.Exists(Path.Combine(root, ".bloons-setup", "app-file-transaction.json")), "Completed recovery left a pending journal");
    }
}
''')
            for crash_at in (1, 2, 3):
                root = Path(folder) / ('crash-' + str(crash_at))
                run = subprocess.run([str(binary), 'crash', str(root), str(crash_at)],
                                     capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 75, run.stdout + run.stderr)
                self.assertEqual((root / 'first.txt').read_text(), 'new first.txt')
                for _ in range(2):
                    retry = subprocess.run([str(binary), 'recover', str(root)],
                                           capture_output=True, text=True, timeout=30)
                    self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
