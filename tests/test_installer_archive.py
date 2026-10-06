import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerArchiveTests(unittest.TestCase):
    def test_later_commit_failure_or_cancellation_restores_the_prior_package(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'PackageRollbackChecks', r'''
using System;
using System.IO;
using System.IO.Compression;
using System.Threading;
internal sealed class LaterCommitFailure : WindowsInstallerOperations {
    private int commits;
    private readonly CancellationTokenSource cancellation;
    private readonly bool outsideChange;
    private readonly bool silentChange;
    public LaterCommitFailure(InstallerOptions options, CancellationTokenSource cancellation, bool outsideChange, bool silentChange) : base(options) {
        this.cancellation = cancellation; this.outsideChange = outsideChange; this.silentChange = silentChange;
    }
    protected override void CommitStagedFile(string staged, string destination) {
        commits++;
        base.CommitStagedFile(staged, destination);
        if (cancellation != null) cancellation.Cancel();
        else if (commits == 2) {
            if (outsideChange) File.WriteAllText(destination, "outside edit");
            if (!silentChange) throw new IOException("Failure after the second replacement");
        }
    }
}
internal static class PackageRollbackChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main(string[] args) {
        foreach (string scenario in new[] {"existing", "new", "cancel", "outside", "silent-change"}) {
            string root = Path.Combine(args[0], scenario); Directory.CreateDirectory(root);
            string first = Path.Combine(root, "first.txt"), second = Path.Combine(root, "second.txt");
            if (scenario != "new") File.WriteAllText(first, "prior first");
            File.WriteAllText(second, "prior second");
            string zip = Path.Combine(args[0], scenario + ".zip");
            using (var output = new FileStream(zip, FileMode.CreateNew))
            using (var archive = new ZipArchive(output, ZipArchiveMode.Create)) {
                using (var writer = new StreamWriter(archive.CreateEntry("first.txt").Open())) writer.Write("new first");
                using (var writer = new StreamWriter(archive.CreateEntry("second.txt").Open())) writer.Write("new second");
            }
            var cancellation = scenario == "cancel" ? new CancellationTokenSource() : null;
            bool changed = scenario == "outside" || scenario == "silent-change";
            using (var operations = new LaterCommitFailure(new InstallerOptions(root, root, "unused.exe", true, null), cancellation, changed, scenario == "silent-change")) {
                if (cancellation != null) operations.Cancellation = cancellation.Token;
                bool stopped = false;
                try { operations.InstallAppFiles(zip); }
                catch (IOException) { stopped = true; }
                catch (OperationCanceledException) { stopped = true; }
                Check(stopped, scenario + ": injected interruption was ignored");
                Check(scenario == "new" ? !File.Exists(first) : File.ReadAllText(first) == "prior first", scenario + ": first replacement was not rolled back");
                Check(File.ReadAllText(second) == (changed ? "outside edit" : "prior second"), scenario + ": second replacement or outside edit was not preserved");
                var backups = Directory.GetFiles(Path.Combine(root, ".bloons-setup"), "*.old", SearchOption.AllDirectories);
                Check(backups.Length == (changed ? 1 : 0), scenario + ": recovery copies were not retained or cleaned correctly");
                if (changed) {
                    Check(File.ReadAllText(backups[0]) == "prior second", "Outside edit lost the verified recovery copy");
                    Check(AppFileTransaction.Pending(root), "Unresolved outside edit lost its recovery journal");
                    // The operator keeps the outside edit in a separate file,
                    // then restores the verified prior file before retrying.
                    File.WriteAllText(Path.Combine(root, "outside-kept.txt"), File.ReadAllText(second));
                    File.Copy(backups[0], second, true);
                    operations.RecoverAppFiles(); operations.RecoverAppFiles();
                    Check(!AppFileTransaction.Pending(root), "Resolved conflict did not finish recovery");
                    Check(File.ReadAllText(Path.Combine(root, "outside-kept.txt")) == "outside edit", "Recovery changed saved outside data");
                }
                else {
                    Check(Directory.GetFiles(root, "*.new", SearchOption.AllDirectories).Length == 0, scenario + ": staging remains after successful rollback");
                    Check(!AppFileTransaction.Pending(root), scenario + ": successful rollback left a pending journal");
                }
            }
        }
    }
}
''')
            run = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_entire_archive_is_validated_and_staged_before_replacing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'PackagePreflightChecks', r'''
using System;
using System.IO;
using System.IO.Compression;
using System.Threading;
internal static class PackagePreflightChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Add(ZipArchive archive, string name, string text) {
        using (var writer = new StreamWriter(archive.CreateEntry(name).Open())) writer.Write(text);
    }
    static void Main(string[] args) {
        foreach (string scenario in new[] {"unsafe", "duplicate", "collision", "cancel"}) {
            string root = Path.Combine(args[0], scenario); Directory.CreateDirectory(root);
            string destination = Path.Combine(root, "existing.txt"); File.WriteAllText(destination, "prior data");
            string zip = Path.Combine(args[0], scenario + ".zip");
            using (var output = new FileStream(zip, FileMode.CreateNew))
            using (var archive = new ZipArchive(output, ZipArchiveMode.Create)) {
                Add(archive, "existing.txt", "new data");
                if (scenario == "unsafe") Add(archive, "../outside.txt", "invalid");
                if (scenario == "duplicate") Add(archive, "EXISTING.txt", "ambiguous");
                if (scenario == "collision") Add(archive, "existing.txt/child.txt", "conflicting file parent");
                if (scenario == "cancel") Add(archive, "later.txt", "more data");
            }
            var cancellation = new CancellationTokenSource();
            using (var operations = new WindowsInstallerOperations(new InstallerOptions(root, root, "unused.exe", true, null))) {
                operations.Cancellation = cancellation.Token;
                if (scenario == "cancel") operations.ProgressChanged += progress => {
                    if (progress.Stage == InstallerStage.Files && progress.Numerator > 0) cancellation.Cancel();
                };
                bool stopped = false;
                try { operations.InstallAppFiles(zip); }
                catch (InvalidDataException) { stopped = true; }
                catch (OperationCanceledException) { stopped = true; }
                catch (IOException) { stopped = true; }
                Check(stopped, scenario + ": invalid or cancelled package was accepted");
                Check(File.ReadAllText(destination) == "prior data", scenario + ": earlier app file changed before package was ready");
                Check(!File.Exists(Path.Combine(root, "later.txt")), scenario + ": uncommitted file was installed");
                Check(Directory.GetFiles(root, "*.tmp", SearchOption.AllDirectories).Length == 0, scenario + ": failed staging remains");
                Check(!File.Exists(Path.Combine(args[0], "outside.txt")), "Unsafe entry escaped installation root");
            }
        }
    }
}
''')
            run = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

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
            int priorPercent = 0;
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
            operations.ProgressChanged += progress => {
                if (progress.Stage != InstallerStage.Files || !progress.Percent.HasValue) return;
                if (progress.Percent == 0) priorPercent = 0;
                Check(progress.Percent >= priorPercent, "Preparation-to-apply progress went backwards");
                if (progress.Percent == 100) Check(File.ReadAllText(destination) == "new data", "App files reported ready before replacement");
                priorPercent = progress.Percent.Value;
            };
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
