using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

// One package intent is persisted before any replacement. Recovery derives
// outcomes from file hashes, so it also works after exit during replacement or
// during rollback. Only the installation owner may begin or recover a journal.
internal sealed class AppFileTransaction {
    internal sealed class Entry {
        public string path { get; set; }
        public string before { get; set; }
        public string after { get; set; }
    }
    private sealed class Journal {
        public int version { get; set; }
        public string id { get; set; }
        public string phase { get; set; }
        public Entry[] files { get; set; }
    }
    private readonly string root, journalPath, work;
    private readonly Journal journal;
    private const int MaxLength = 8 * 1024 * 1024;
    private AppFileTransaction(string root, Journal journal) {
        this.root = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar);
        this.journal = journal;
        journalPath = Path.Combine(this.root, ".bloons-setup", "app-file-transaction.json");
        work = Path.Combine(this.root, ".bloons-setup", "files-" + journal.id);
    }
    public static bool Pending(string root) {
        string file = Path.Combine(root, ".bloons-setup", "app-file-transaction.json");
        return File.Exists(file) || Directory.Exists(file) || File.Exists(file + ".next") || Directory.Exists(file + ".next");
    }
    internal static void RequireNoLinks(string target) {
        for (string part = Path.GetFullPath(target); part != null; part = Path.GetDirectoryName(part)) {
            try {
                if ((File.GetAttributes(part) & FileAttributes.ReparsePoint) != 0)
                    throw new InvalidDataException("Installer recovery crosses a linked path. Keep the files and repair the installation location.");
            } catch (FileNotFoundException) {} catch (DirectoryNotFoundException) {}
        }
    }
    internal static string Destination(string root, string relative) {
        if (String.IsNullOrEmpty(relative) || Path.IsPathRooted(relative) || relative.Contains(":"))
            throw new InvalidDataException("Invalid installer app-file path.");
        string normalized = relative.Replace('/', '\\').TrimEnd('\\');
        foreach (string part in normalized.Split('\\')) {
            if (String.IsNullOrEmpty(part) || part == "." || part == ".." || part.EndsWith(".") || part.EndsWith(" ")
                || Regex.IsMatch(part, @"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)", RegexOptions.IgnoreCase))
                throw new InvalidDataException("Invalid installer app-file path.");
        }
        if (String.Equals(normalized.Split('\\')[0], ".bloons-setup", StringComparison.OrdinalIgnoreCase)
            || String.Equals(normalized, ".bloons-install.lock", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Installer package contains a reserved recovery path.");
        string prefix = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        string destination = Path.GetFullPath(Path.Combine(prefix, normalized));
        if (!destination.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Installer app-file path leaves its installation.");
        RequireNoLinks(destination);
        return destination;
    }
    internal static string Hash(string file) {
        RequireNoLinks(file);
        using (SHA256 hash = SHA256.Create())
        using (FileStream input = File.OpenRead(file)) return BitConverter.ToString(hash.ComputeHash(input));
    }
    private static bool ValidHash(string hash) { return Regex.IsMatch(hash ?? "", @"^[0-9A-F]{2}(-[0-9A-F]{2}){31}$"); }
    private void Validate() {
        Guid id;
        if (journal.version != 1 || !Guid.TryParseExact(journal.id, "N", out id)
            || !new[] { "preparing", "prepared", "committed" }.Contains(journal.phase)
            || journal.files == null || journal.files.Length > 20000
            || (journal.phase == "preparing" && journal.files.Length != 0))
            throw new InvalidDataException("Installer app-file recovery journal is invalid. Files were retained.");
        RequireNoLinks(journalPath); RequireNoLinks(journalPath + ".next"); RequireNoLinks(work);
        var paths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (Entry entry in journal.files) {
            if (entry == null || !ValidHash(entry.after) || (entry.before != null && !ValidHash(entry.before))
                || !paths.Add(Destination(root, entry.path)))
                throw new InvalidDataException("Installer app-file recovery entry is invalid. Files were retained.");
        }
        foreach (string file in paths) for (string parent = Path.GetDirectoryName(file); parent != null; parent = Path.GetDirectoryName(parent)) {
            if (paths.Contains(parent)) throw new InvalidDataException("Installer recovery uses a file as a directory. Files were retained.");
            if (String.Equals(parent, root, StringComparison.OrdinalIgnoreCase)) break;
        }
        // Validate every recovery artifact before replacing or deleting anything.
        if (Directory.Exists(work)) foreach (string file in Directory.GetFileSystemEntries(work)) {
            RequireNoLinks(file);
            var name = Regex.Match(Path.GetFileName(file), @"^(0|[1-9][0-9]*)\.(new|old)$");
            int index;
            if (Directory.Exists(file) || !name.Success || !Int32.TryParse(name.Groups[1].Value, out index)
                || index >= (journal.phase == "preparing" ? 20000 : journal.files.Length))
                throw new InvalidDataException("Installer recovery contains an unrecognized file. Files were retained.");
        }
    }
    private void Save() {
        Validate();
        string text = new JavaScriptSerializer { MaxJsonLength = MaxLength }.Serialize(journal);
        byte[] bytes = Encoding.UTF8.GetBytes(text);
        if (bytes.Length > MaxLength) throw new InvalidDataException("Installer recovery journal exceeds its size limit.");
        using (var output = new FileStream(journalPath + ".next", FileMode.Create, FileAccess.Write, FileShare.None)) {
            output.Write(bytes, 0, bytes.Length); output.Flush(true);
        }
        if (File.Exists(journalPath)) File.Replace(journalPath + ".next", journalPath, null);
        else File.Move(journalPath + ".next", journalPath);
    }
    public static AppFileTransaction Begin(string root) {
        if (Pending(root)) throw new IOException("An app-file transaction needs recovery before setup can continue.");
        var transaction = new AppFileTransaction(root, new Journal { version = 1, id = Guid.NewGuid().ToString("N"), phase = "preparing", files = new Entry[0] });
        transaction.Validate();
        Directory.CreateDirectory(Path.GetDirectoryName(transaction.journalPath));
        transaction.Save(); // No app changes or staging directory exist before this durable intent.
        Directory.CreateDirectory(transaction.work);
        return transaction;
    }
    public string StagedPath(int index) { return WorkPath(index, ".new"); }
    public string BackupPath(int index) { return WorkPath(index, ".old"); }
    private string WorkPath(int index, string suffix) {
        if (index < 0 || index >= 20000) throw new InvalidDataException("Installer app-file count exceeds its limit.");
        string path = Path.Combine(work, index.ToString(System.Globalization.CultureInfo.InvariantCulture) + suffix);
        RequireNoLinks(path); return path;
    }
    public void Prepare(Entry[] entries) {
        journal.files = entries; journal.phase = "prepared"; Validate();
        for (int i = 0; i < entries.Length; i++) {
            if (Hash(StagedPath(i)) != entries[i].after || (entries[i].before != null && Hash(BackupPath(i)) != entries[i].before))
                throw new IOException("An app-file recovery artifact changed before commit. Retry setup.");
        }
        Save();
    }
    public void Complete() {
        Validate();
        foreach (Entry entry in journal.files) {
            string destination = Destination(root, entry.path);
            if (!File.Exists(destination) || Hash(destination) != entry.after)
                throw new IOException("An installed app file changed before setup finished. Its recovery copy is retained.");
        }
        journal.phase = "committed"; Save();
        Cleanup();
    }
    private void Cleanup() {
        Validate();
        if (Directory.Exists(work)) {
            foreach (string file in Directory.GetFiles(work)) File.Delete(file);
            Directory.Delete(work, false);
        }
        if (File.Exists(journalPath + ".next")) File.Delete(journalPath + ".next");
        File.Delete(journalPath); // Last: a crash during cleanup remains recoverable.
    }
    public static void Recover(string root) {
        string path = Path.Combine(root, ".bloons-setup", "app-file-transaction.json");
        if (!Pending(root)) return;
        RequireNoLinks(path); RequireNoLinks(path + ".next");
        string source = File.Exists(path) ? path : path + ".next";
        if (new FileInfo(source).Length > MaxLength) throw new InvalidDataException("Installer recovery journal exceeds its size limit.");
        Journal journal;
        try { journal = new JavaScriptSerializer { MaxJsonLength = MaxLength }.Deserialize<Journal>(File.ReadAllText(source)); }
        catch (ArgumentException error) { throw new InvalidDataException("Installer recovery journal could not be read. Files were retained.", error); }
        Guid id;
        if (journal == null || !Guid.TryParseExact(journal.id, "N", out id))
            throw new InvalidDataException("Installer recovery identifier is invalid. Files were retained.");
        var transaction = new AppFileTransaction(root, journal); transaction.Validate();
        if (journal.phase == "prepared") {
            var errors = new List<Exception>();
            for (int i = journal.files.Length - 1; i >= 0; i--) {
                try { transaction.Restore(i); } catch (Exception error) { errors.Add(error); }
            }
            if (errors.Count > 0) throw new IOException("App file recovery could not finish. Recovery copies were retained; close the app and retry setup. Changed files are preserved.", new AggregateException(errors));
        }
        transaction.Cleanup(); // Preparing changed no app files; committed keeps the new package.
    }
    private void Restore(int index) {
        Entry entry = journal.files[index];
        string destination = Destination(root, entry.path);
        string current = File.Exists(destination) ? Hash(destination) : null;
        if (current == entry.before) return;
        if (current != entry.after && current != null)
            throw new IOException("An app file changed outside setup; its recovery copy was retained.");
        if (entry.before == null) { if (File.Exists(destination)) File.Delete(destination); return; }
        string backup = BackupPath(index);
        if (!File.Exists(backup) || Hash(backup) != entry.before)
            throw new IOException("An app recovery copy could not be verified.");
        Directory.CreateDirectory(Path.GetDirectoryName(destination));
        if (File.Exists(destination)) File.Replace(backup, destination, null);
        else File.Move(backup, destination);
    }
}
