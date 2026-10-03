using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Drawing;
using System.Diagnostics;
using System.Net;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Drawing.Drawing2D;

internal sealed class InstallerForm : Form
{
    private readonly Label status = new Label();
    private readonly ProgressBar progress = new ProgressBar();
    private readonly Button installButton = new Button();
    private readonly Label introduction = new Label();
    private readonly CheckBox vmSetup = new CheckBox();
    private readonly TextBox isoPath = new TextBox();
    private readonly Label isoLabel = new Label();
    private readonly Button browseIso = new Button();
    private readonly Label progressCaption = new Label();
    private bool requestedVmSetup = true;
    private string requestedIsoPath = "";
    private readonly bool silent = Environment.GetCommandLineArgs().Any(arg => String.Equals(arg, "/silent", StringComparison.OrdinalIgnoreCase));
    private readonly string installRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Bloons+");

    public InstallerForm()
    {
        Text = "Bloons+ Setup";
        Width = 650;
        Height = 420;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = true;
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Color.FromArgb(237, 242, 251);

        var brand = new Panel { Left = 0, Top = 0, Width = 650, Height = 92, BackColor = Color.FromArgb(30, 42, 82) };
        var logo = new Label { Left = 28, Top = 18, Width = 54, Height = 54, Text = "+", TextAlign = ContentAlignment.MiddleCenter,
            BackColor = Color.FromArgb(93, 214, 184), ForeColor = Color.FromArgb(24, 48, 76), Font = new Font("Segoe UI", 25, FontStyle.Bold) };
        brand.Controls.Add(logo);
        var brandTitle = new Label { Left = 96, Top = 16, Width = 500, Height = 34, Text = "Bloons+", ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 21, FontStyle.Bold) };
        brand.Controls.Add(brandTitle);
        var brandSub = new Label { Left = 98, Top = 50, Width = 500, Height = 22, Text = "A cleaner way to run and manage your BTD6 setup", ForeColor = Color.FromArgb(190, 207, 238), Font = new Font("Segoe UI", 9) };
        brand.Controls.Add(brandSub); Controls.Add(brand);

        introduction.Text = "Welcome\r\nInstall the app, then finish the guided setup from Settings. Your existing progress is preserved.";
        introduction.Left = 28;
        introduction.Top = 108;
        introduction.Width = 580;
        introduction.Height = 116;
        introduction.Font = new Font("Segoe UI", 11, FontStyle.Regular);
        introduction.ForeColor = Color.FromArgb(28, 43, 74);
        Controls.Add(introduction);

        vmSetup.Text = "Set up the VM, Steam and BTD6 after installation";
        vmSetup.Checked = true;
        vmSetup.Left = 28;
        vmSetup.Top = 178;
        vmSetup.Width = 565;
        vmSetup.Height = 27;
        vmSetup.Font = new Font("Segoe UI", 10, FontStyle.Regular);
        Controls.Add(vmSetup);

        isoLabel.Text = "Have a Windows 11 ISO? Choose it here, or leave blank for guided setup.";
        isoLabel.Left = 28;
        isoLabel.Top = 208;
        isoLabel.Width = 580;
        isoLabel.Height = 16;
        isoLabel.ForeColor = Color.FromArgb(90, 107, 140);
        isoLabel.Font = new Font("Segoe UI", 8, FontStyle.Bold);
        Controls.Add(isoLabel);
        isoPath.Left = 28;
        isoPath.Top = 227;
        isoPath.Width = 470;
        isoPath.Height = 30;
        isoPath.Font = new Font("Segoe UI", 9, FontStyle.Regular);
        Controls.Add(isoPath);
        browseIso.Text = "Browse…";
        browseIso.SetBounds(510, 225, 98, 30);
        browseIso.Click += delegate {
            using (var picker = new OpenFileDialog()) {
                picker.Title = "Choose a Windows 11 ISO";
                picker.Filter = "Windows ISO (*.iso)|*.iso";
                if (picker.ShowDialog(this) == DialogResult.OK) isoPath.Text = picker.FileName;
            }
        };
        Controls.Add(browseIso);
        vmSetup.CheckedChanged += delegate {
            isoPath.Enabled = browseIso.Enabled = isoLabel.Enabled = vmSetup.Checked;
        };

        status.Text = File.Exists(Path.Combine(installRoot, "Bloons+.exe")) ? "Existing installation found. Changed files only will be updated." : "Ready to install Bloons+.";
        status.AutoSize = false;
        status.Left = 22;
        status.Top = 270;
        status.Width = 580;
        status.Height = 28;
        status.Font = new Font("Segoe UI", 10, FontStyle.Regular);
        Controls.Add(status);

        progress.Left = 22;
        progress.Top = 310;
        progress.Width = 580;
        progress.Height = 22;
        progress.Minimum = 0;
        progress.Maximum = 1000;
        Controls.Add(progress);

        installButton.Text = File.Exists(Path.Combine(installRoot, "Bloons+.exe")) ? "Update Bloons+" : "Install Bloons+";
        installButton.Left = 435;
        installButton.Top = 348;
        installButton.Width = 173;
        installButton.Height = 42;
        installButton.FlatStyle = FlatStyle.Flat;
        installButton.BackColor = Color.FromArgb(62, 90, 207);
        installButton.ForeColor = Color.White;
        installButton.Font = new Font("Segoe UI Semibold", 10, FontStyle.Bold);
        installButton.Click += delegate {
            requestedVmSetup = vmSetup.Checked;
            requestedIsoPath = requestedVmSetup ? isoPath.Text.Trim() : "";
            if (requestedIsoPath.Length > 0 && !File.Exists(requestedIsoPath)) {
                MessageBox.Show(this, "The selected Windows ISO does not exist. Choose a valid file or leave the field empty to download one during setup.", "Bloons+ Setup", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            installButton.Enabled = false;
            vmSetup.Enabled = isoPath.Enabled = browseIso.Enabled = false;
            Task.Run((Action)Install);
        };
        Controls.Add(installButton);
        ApplyGlassLayout(brand);
        if (silent) {
            ShowInTaskbar = false;
            WindowState = FormWindowState.Minimized;
            requestedVmSetup = false;
            Shown += delegate { installButton.Enabled = false; Task.Run((Action)Install); };
        }
    }

    private void ApplyGlassLayout(Panel oldHeader)
    {
        Controls.Remove(oldHeader);
        oldHeader.Dispose();
        DoubleBuffered = true;
        AutoScaleMode = AutoScaleMode.Dpi;
        ClientSize = new Size(860, 600);
        Font = new Font("Segoe UI", 10);
        ForeColor = Color.FromArgb(34, 44, 64);
        introduction.Text = "Make yourself at home.";
        introduction.SetBounds(306, 49, 510, 44);
        introduction.Font = new Font("Segoe UI", 25, FontStyle.Bold);
        introduction.BackColor = Color.Transparent;
        AddCopy("Your Bloons+ setup, one step at a time.", 309, 102, 470, 30, 11, false);
        AddCopy("Bloons+", 49, 59, 196, 44, 27, true);
        AddCopy("YOUR GAME. YOUR SPACE.", 51, 110, 195, 24, 8, true);
        AddCopy("01   Install the app", 50, 195, 215, 32, 12, true);
        AddCopy("Files and required components", 50, 230, 207, 40, 9, false);
        AddCopy("02   Prepare your VM", 50, 295, 215, 32, 12, true);
        AddCopy("Continue in the guided setup", 50, 330, 207, 40, 9, false);
        AddCopy("03   Connect Steam", 50, 395, 215, 32, 12, true);
        AddCopy("Sign in and install your BTD6", 50, 430, 207, 40, 9, false);
        AddCopy("MADE FOR YOUR DESKTOP", 50, 534, 218, 22, 8, true);
        AddCopy("SETUP PREFERENCES", 329, 167, 450, 24, 9, true);
        vmSetup.SetBounds(329, 207, 450, 31);
        vmSetup.Text = "Continue with guided VM setup";
        vmSetup.BackColor = Color.FromArgb(245, 247, 253);
        isoLabel.Text = "Windows 11 ISO · optional";
        isoLabel.SetBounds(329, 258, 440, 25);
        isoLabel.BackColor = vmSetup.BackColor;
        isoPath.SetBounds(329, 291, 328, 30);
        browseIso.SetBounds(673, 285, 106, 40);
        StyleButton(browseIso, false);
        AddCopy("Leave empty to download Windows during guided setup.", 329, 339, 454, 27, 9, false);
        status.SetBounds(329, 409, 447, 48);
        status.BackColor = Color.FromArgb(245, 247, 253);
        status.Font = new Font("Segoe UI", 10);
        progress.SetBounds(329, 470, 447, 8);
        progress.Visible = false;
        progressCaption.SetBounds(329, 489, 447, 25);
        progressCaption.Text = "Ready when you are";
        progressCaption.Font = new Font("Segoe UI", 9);
        progressCaption.ForeColor = Color.FromArgb(102, 115, 138);
        progressCaption.BackColor = Color.Transparent;
        Controls.Add(progressCaption);
        installButton.SetBounds(594, 535, 213, 43);
        StyleButton(installButton, true);
        AcceptButton = installButton;
        AddCopy("Your existing progress stays saved.", 309, 547, 280, 25, 9, false);
    }

    private void AddCopy(string text, int x, int y, int width, int height, float size, bool bold)
    {
        Controls.Add(new Label { Text = text, Left = x, Top = y, Width = width, Height = height,
            BackColor = Color.Transparent, ForeColor = bold ? Color.FromArgb(34, 44, 64) : Color.FromArgb(102, 115, 138),
            Font = new Font("Segoe UI", size, bold ? FontStyle.Bold : FontStyle.Regular) });
    }

    private static GraphicsPath Rounded(Rectangle r, int radius)
    {
        var p = new GraphicsPath(); int d = radius * 2;
        p.AddArc(r.Left, r.Top, d, d, 180, 90); p.AddArc(r.Right-d, r.Top, d, d, 270, 90);
        p.AddArc(r.Right-d, r.Bottom-d, d, d, 0, 90); p.AddArc(r.Left, r.Bottom-d, d, d, 90, 90);
        p.CloseFigure(); return p;
    }

    private static void StyleButton(Button button, bool primary)
    {
        button.FlatStyle = FlatStyle.Flat; button.FlatAppearance.BorderSize = 0;
        button.BackColor = primary ? Color.FromArgb(85, 120, 218) : Color.FromArgb(229, 236, 250);
        button.ForeColor = primary ? Color.White : Color.FromArgb(65, 86, 131);
        button.Font = new Font("Segoe UI", 10, FontStyle.Bold);
        button.Cursor = Cursors.Hand;
        using (var p = Rounded(new Rectangle(0, 0, button.Width, button.Height), 12)) button.Region = new Region(p);
    }

    protected override void OnPaintBackground(PaintEventArgs e)
    {
        using (var bg = new LinearGradientBrush(ClientRectangle, Color.FromArgb(226, 223, 242), Color.FromArgb(221, 238, 247), 35f))
            e.Graphics.FillRectangle(bg, ClientRectangle);
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        foreach (var rect in new[] { new Rectangle(24, 24, 254, 552), new Rectangle(306, 148, 501, 235), new Rectangle(306, 393, 501, 128) })
        {
            using (var shadow = Rounded(new Rectangle(rect.X, rect.Y+5, rect.Width, rect.Height), 22))
            using (var brush = new SolidBrush(Color.FromArgb(12, 53, 76, 112))) e.Graphics.FillPath(brush, shadow);
            using (var shape = Rounded(rect, 22))
            using (var fill = new SolidBrush(Color.FromArgb(155, 255, 255, 255)))
            using (var border = new Pen(Color.FromArgb(220, 255, 255, 255)))
            { e.Graphics.FillPath(fill, shape); e.Graphics.DrawPath(border, shape); }
        }
        using (var track = Rounded(new Rectangle(329, 470, 447, 8), 4))
        using (var brush = new SolidBrush(Color.FromArgb(218, 225, 241))) e.Graphics.FillPath(brush, track);
        int width = (int)(447L * progress.Value / 1000);
        if (width >= 8) using (var fill = Rounded(new Rectangle(329, 470, width, 8), 4))
        using (var brush = new LinearGradientBrush(new Rectangle(329, 470, 447, 8), Color.FromArgb(85,120,218), Color.FromArgb(138,156,231), 0f)) e.Graphics.FillPath(brush, fill);
    }

    private void SetStatus(string text, int value)
    {
        if (IsDisposed) return;
        BeginInvoke((Action)delegate
        {
            status.Text = text;
            progress.Value = Math.Max(progress.Minimum, Math.Min(progress.Maximum, value));
            progressCaption.Text = value >= 1000 ? "App installed · opening guided setup" : (value / 10).ToString() + "% · App installation";
            Invalidate();
        });
    }

    private static string SafeDestination(string root, string entryName)
    {
        string normalized = entryName.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar);
        string destination = Path.GetFullPath(Path.Combine(root, normalized));
        string prefix = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!destination.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Installer archive contains an invalid path.");
        return destination;
    }

    private static string HashFile(string file)
    {
        using (SHA256 hash = SHA256.Create())
        using (FileStream input = File.OpenRead(file))
            return BitConverter.ToString(hash.ComputeHash(input));
    }

    private static bool SameAsArchiveEntry(ZipArchiveEntry entry, string destination)
    {
        if (!File.Exists(destination) || new FileInfo(destination).Length != entry.Length) return false;
        using (SHA256 hash = SHA256.Create())
        using (Stream input = entry.Open())
            return BitConverter.ToString(hash.ComputeHash(input)) == HashFile(destination);
    }

    private void BackupExistingData(string backupRoot)
    {
        string[] preserve = {
            "resources/app/automation-progress.json",
            "resources/app/game-observations.json",
            "resources/app/calibration.json",
            "resources/app/map-order.json",
            "resources/app/route-verification.json",
            "resources/app/autobtd6/userconfig.json",
            "resources/app/autobtd6/playthrough_stats.json"
        };
        foreach (string relative in preserve)
        {
            string source = SafeDestination(installRoot, relative);
            if (!File.Exists(source)) continue;
            string destination = SafeDestination(backupRoot, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(source, destination, true);
        }
        string[] preserveDirectories = { "resources/app/route-library", "resources/app/autobtd6/playthroughs" };
        foreach (string relative in preserveDirectories)
        {
            string source = SafeDestination(installRoot, relative);
            if (!Directory.Exists(source)) continue;
            string destination = SafeDestination(backupRoot, relative);
            CopyDirectory(source, destination);
        }
    }

    private static void CopyDirectory(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (string directory in Directory.GetDirectories(source, "*", SearchOption.AllDirectories))
            Directory.CreateDirectory(Path.Combine(destination, directory.Substring(source.Length).TrimStart(Path.DirectorySeparatorChar)));
        foreach (string file in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string target = Path.Combine(destination, file.Substring(source.Length).TrimStart(Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            File.Copy(file, target, true);
        }
    }

    private void RestoreExistingData(string backupRoot)
    {
        if (!Directory.Exists(backupRoot)) return;
        foreach (string file in Directory.GetFiles(backupRoot, "*", SearchOption.AllDirectories))
        {
            string relative = file.Substring(backupRoot.Length).TrimStart(Path.DirectorySeparatorChar);
            string destination = Path.Combine(installRoot, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(file, destination, true);
        }
    }

    private void Install()
    {
        string tempZip = Path.Combine(Path.GetTempPath(), "BloonsPlus-" + Guid.NewGuid().ToString("N") + ".zip");
        string backupRoot = Path.Combine(Path.GetTempPath(), "BloonsPlus-data-" + Guid.NewGuid().ToString("N"));
        try
        {
            SetStatus("Reading embedded app package…", 0);
            using (FileStream installer = new FileStream(Application.ExecutablePath, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                if (installer.Length < 16) throw new InvalidDataException("The installer package is incomplete.");
                installer.Seek(-16, SeekOrigin.End);
                byte[] footer = new byte[16];
                installer.Read(footer, 0, footer.Length);
                string marker = Encoding.ASCII.GetString(footer, 0, 8);
                long zipLength = BitConverter.ToInt64(footer, 8);
                long zipOffset = installer.Length - 16 - zipLength;
                if (marker != "BLPZIP01" || zipLength <= 0 || zipOffset <= 0)
                    throw new InvalidDataException("The embedded app package could not be located.");
                installer.Seek(zipOffset, SeekOrigin.Begin);
                using (FileStream zipFile = new FileStream(tempZip, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                {
                    byte[] buffer = new byte[1024 * 1024];
                    long remaining = zipLength;
                    while (remaining > 0)
                    {
                        int read = installer.Read(buffer, 0, (int)Math.Min(buffer.Length, remaining));
                        if (read <= 0) throw new EndOfStreamException("The embedded app package ended early.");
                        zipFile.Write(buffer, 0, read);
                        remaining -= read;
                    }
                }
            }

            Directory.CreateDirectory(installRoot);
            BackupExistingData(backupRoot);
            SetStatus("Installing Bloons+ files…", 5);
            bool useInstalledPython = FindCompatiblePython() != null;
            using (FileStream package = new FileStream(tempZip, FileMode.Open, FileAccess.Read, FileShare.Read))
            using (ZipArchive archive = new ZipArchive(package, ZipArchiveMode.Read))
            {
                long totalBytes = Math.Max(1, archive.Entries.Sum(entry => entry.Length));
                long writtenBytes = 0;
                int reusedFiles = 0;
                byte[] buffer = new byte[1024 * 1024];
                foreach (ZipArchiveEntry entry in archive.Entries)
                {
                    if (useInstalledPython && entry.FullName.StartsWith("resources/app/python/", StringComparison.OrdinalIgnoreCase)) {
                        writtenBytes += entry.Length;
                        continue;
                    }
                    string destination = SafeDestination(installRoot, entry.FullName);
                    if (entry.FullName.EndsWith("/", StringComparison.Ordinal) || entry.FullName.EndsWith("\\", StringComparison.Ordinal))
                    {
                        Directory.CreateDirectory(destination);
                        continue;
                    }
                    if (SameAsArchiveEntry(entry, destination)) {
                        writtenBytes += entry.Length;
                        reusedFiles++;
                        continue;
                    }
                    Directory.CreateDirectory(Path.GetDirectoryName(destination));
                    using (Stream input = entry.Open())
                    using (FileStream output = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None))
                    {
                        int read;
                        while ((read = input.Read(buffer, 0, buffer.Length)) > 0)
                        {
                            output.Write(buffer, 0, read);
                            writtenBytes += read;
                        }
                    }
                    if (writtenBytes % (64L * 1024 * 1024) < buffer.Length)
                        SetStatus("Installing Bloons+ files… " + (writtenBytes / (1024 * 1024)).ToString("N0") + " MB", 5 + (int)(writtenBytes * 920 / totalBytes));
                }
                SetStatus("App files ready; reused " + reusedFiles + " unchanged files.", 950);
            }

            RestoreExistingData(backupRoot);
            SetStatus("Finalizing Python runtime and shortcuts…", 960);
            EnsureVisualCppRuntime();
            ConfigurePython();
            CreateStartMenuShortcut();
            KeepInstallerCopy();
            SaveSetupIntent();
            SetStatus("Bloons+ is installed. Launching the app…", 1000);
            Process.Start(new ProcessStartInfo(Path.Combine(installRoot, "Bloons+.exe")) { WorkingDirectory = installRoot, UseShellExecute = true });
            Task.Delay(1800).ContinueWith(delegate { if (!IsDisposed) BeginInvoke((Action)Close); });
        }
        catch (Exception error)
        {
            SetStatus("Installation failed: " + error.Message, 0);
            if (!IsDisposed && IsHandleCreated)
                BeginInvoke((Action)delegate {
                    installButton.Enabled = vmSetup.Enabled = true;
                    isoPath.Enabled = browseIso.Enabled = vmSetup.Checked;
                    installButton.Text = "Retry installation";
                    MessageBox.Show(this, "Setup paused. You can change your options and retry.\r\n\r\n" + error.Message, "Bloons+ Setup", MessageBoxButtons.OK, MessageBoxIcon.Error);
                });
        }
        finally
        {
            try { if (File.Exists(tempZip)) File.Delete(tempZip); } catch { }
            try { if (Directory.Exists(backupRoot)) Directory.Delete(backupRoot, true); } catch { }
        }
    }

    private void ConfigurePython()
    {
        string appRoot = Path.Combine(installRoot, "resources", "app");
        string python = FindCompatiblePython() ?? Path.Combine(appRoot, "python", "python.exe");
        string venv = Path.Combine(appRoot, ".venv");
        string pipRequirements = Path.Combine(appRoot, "requirements-installer.txt");
        if (!File.Exists(python) || !File.Exists(pipRequirements))
            throw new FileNotFoundException("A compatible Python 3.12 runtime or the bundled fallback is required.");

        string driveRoot = Path.GetPathRoot(installRoot);
        if (new DriveInfo(driveRoot).AvailableFreeSpace < 5L * 1024 * 1024 * 1024)
            throw new IOException("At least 5 GB of free disk space is needed to install the automation runtime.");

        string venvPython = Path.Combine(venv, "Scripts", "python.exe");
        if (!File.Exists(venvPython)) {
            SetStatus("Creating Bloons+’s private Python environment…", 965);
            RunInstallerProcess(python, "-m venv " + Quote(venv), appRoot, "Could not create the private Python environment");
        }
        if (!File.Exists(venvPython)) throw new FileNotFoundException("The private Python environment was not created.");
        string stamp = Path.Combine(venv, "bloons-requirements.sha256");
        string requirementsHash = HashFile(pipRequirements);
        string installedCheck = "-c \"from importlib import metadata as m;import sys;lines=[x.strip().split('==',1) for x in open(sys.argv[1]) if '==' in x];assert all(m.version(n)==v for n,v in lines)\" " + Quote(pipRequirements);
        if (File.Exists(stamp) && File.ReadAllText(stamp).Trim() == requirementsHash &&
            ProcessSucceeds(venvPython, installedCheck) && ProcessSucceeds(venvPython, "-m pip check")) {
            SetStatus("Existing Python packages are ready.", 985);
            return;
        }
        SetStatus("Downloading Python dependencies (including TensorFlow); this may take a while…", 975);
        RunInstallerProcess(venvPython, "-m pip install --disable-pip-version-check --no-input -r " + Quote(pipRequirements), appRoot, "Python dependency installation failed");
        File.WriteAllText(stamp, requirementsHash);
    }

    private void EnsureVisualCppRuntime()
    {
        string system = Environment.GetFolderPath(Environment.SpecialFolder.System);
        string runtime = Path.Combine(system, "msvcp140.dll");
        string runtime1 = Path.Combine(system, "msvcp140_1.dll");
        if (File.Exists(runtime) && File.Exists(runtime1)) {
            SetStatus("Microsoft C++ runtime is ready.", 945);
            return;
        }
        SetStatus("Downloading the Microsoft C++ runtime required by TensorFlow…", 930);
        string installer = Path.Combine(Path.GetTempPath(), "BloonsPlus-vc_redist.x64.exe");
        try {
            // .NET Framework can otherwise negotiate legacy TLS on older Windows installs,
            // which makes Microsoft's current aka.ms endpoint fail before setup begins.
            ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072; // TLS 1.2
            using (WebClient client = new WebClient())
                client.DownloadFile("https://aka.ms/vs/17/release/vc_redist.x64.exe", installer);
            SetStatus("Installing the Microsoft C++ runtime (Windows may ask for permission)…", 940);
            ProcessStartInfo start = new ProcessStartInfo(installer, "/install /quiet /norestart") {
                UseShellExecute = true, Verb = "runas", WindowStyle = ProcessWindowStyle.Hidden
            };
            using (Process child = Process.Start(start)) {
                child.WaitForExit();
                if (child.ExitCode != 0 && child.ExitCode != 1638 && child.ExitCode != 3010)
                    throw new InvalidOperationException("Microsoft C++ runtime setup exited with code " + child.ExitCode + ".");
            }
        }
        catch (System.ComponentModel.Win32Exception error) {
            throw new InvalidOperationException("Microsoft C++ runtime installation was cancelled or blocked: " + error.Message);
        }
        finally { try { if (File.Exists(installer)) File.Delete(installer); } catch { } }
        if (!File.Exists(runtime) || !File.Exists(runtime1))
            throw new InvalidOperationException("Microsoft C++ runtime installation finished, but msvcp140.dll and msvcp140_1.dll are still missing. Restart Windows, then run setup again.");
    }

    private static bool ProcessSucceeds(string file, string arguments)
    {
        try {
            using (Process child = Process.Start(new ProcessStartInfo(file, arguments) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true })) {
                child.StandardOutput.ReadToEnd(); child.StandardError.ReadToEnd();
                return child.WaitForExit(10000) && child.ExitCode == 0;
            }
        } catch { return false; }
    }

    private static string FindCompatiblePython()
    {
        string[] candidates = {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python312", "python.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Python312", "python.exe")
        };
        foreach (string candidate in candidates)
            if (File.Exists(candidate) && ProcessSucceeds(candidate, "-c \"import sys; assert sys.version_info[:2] == (3,12) and sys.maxsize > 2**32\"")) return candidate;
        // PATH Python is also accepted, but Windows Store aliases that do not run are ignored.
        foreach (string command in new[] { "py.exe", "python.exe" }) {
            string resolved = ResolvePython(command, command == "py.exe" ? "-3.12 " : "");
            if (resolved != null) return resolved;
        }
        return null;
    }

    private static string ResolvePython(string command, string prefix)
    {
        try {
            using (Process child = Process.Start(new ProcessStartInfo(command, prefix + "-c \"import sys; assert sys.version_info[:2] == (3,12) and sys.maxsize > 2**32; print(sys.executable)\"") {
                UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true })) {
                string path = child.StandardOutput.ReadToEnd().Trim();
                child.StandardError.ReadToEnd();
                if (child.WaitForExit(10000) && child.ExitCode == 0 && File.Exists(path)) return path;
            }
        } catch { /* not installed */ }
        return null;
    }

    private static string Quote(string value) { return "\"" + value.Replace("\"", "\\\"") + "\""; }

    private void RunInstallerProcess(string executable, string arguments, string workingDirectory, string errorPrefix)
    {
        ProcessStartInfo start = new ProcessStartInfo(executable, arguments);
        start.WorkingDirectory = workingDirectory;
        start.UseShellExecute = false;
        start.CreateNoWindow = true;
        start.RedirectStandardOutput = true;
        start.RedirectStandardError = true;
        Process child = new Process();
        child.StartInfo = start;
        string lastOutput = "";
        child.OutputDataReceived += delegate(object sender, DataReceivedEventArgs eventArgs)
        {
            if (!String.IsNullOrWhiteSpace(eventArgs.Data))
            {
                lastOutput = eventArgs.Data;
                if (eventArgs.Data.IndexOf("Downloading", StringComparison.OrdinalIgnoreCase) >= 0 || eventArgs.Data.IndexOf("Installing", StringComparison.OrdinalIgnoreCase) >= 0 || eventArgs.Data.IndexOf("Successfully installed", StringComparison.OrdinalIgnoreCase) >= 0)
                    SetStatus(eventArgs.Data.Length > 80 ? eventArgs.Data.Substring(0, 77) + "…" : eventArgs.Data, 980);
            }
        };
        child.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs eventArgs)
        {
            if (!String.IsNullOrWhiteSpace(eventArgs.Data)) lastOutput = eventArgs.Data;
        };
        child.Start();
        child.BeginOutputReadLine();
        child.BeginErrorReadLine();
        child.WaitForExit();
        child.WaitForExit();
        if (child.ExitCode != 0) throw new InvalidOperationException(errorPrefix + ": " + lastOutput);
    }

    // The Setup bar installs Bloons+ inside the VM from this copy (an installed PC has no dist/ folder).
    private void KeepInstallerCopy()
    {
        string source = Path.GetFullPath(Application.ExecutablePath);
        string target = Path.Combine(installRoot, "BloonsPlusSetup.exe");
        if (String.Equals(source, Path.GetFullPath(target), StringComparison.OrdinalIgnoreCase)) return;
        SetStatus("Keeping a copy of the installer for the VM setup…", 990);
        if (!File.Exists(target) || HashFile(source) != HashFile(target)) File.Copy(source, target, true);
    }

    private void SaveSetupIntent()
    {
        if (silent) return;
        string dataRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "BloonsPlus");
        Directory.CreateDirectory(dataRoot);
        string intent = Path.Combine(dataRoot, "auto-setup.txt");
        if (requestedVmSetup) File.WriteAllText(intent, requestedIsoPath);
        else if (File.Exists(intent)) File.Delete(intent);
    }

    private void CreateStartMenuShortcut()
    {
        string programs = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
        Directory.CreateDirectory(programs);
        string shortcutPath = Path.Combine(programs, "Bloons+.lnk");
        Type shellType = Type.GetTypeFromProgID("WScript.Shell");
        if (shellType == null) return;
        object shell = Activator.CreateInstance(shellType);
        try
        {
            dynamic script = shell;
            dynamic shortcut = script.CreateShortcut(shortcutPath);
            shortcut.TargetPath = Path.Combine(installRoot, "Bloons+.exe");
            shortcut.WorkingDirectory = installRoot;
            shortcut.Description = "Bloons+ BTD6 companion";
            string iconPath = Path.Combine(installRoot, "resources", "app", "bloonsplus.ico");
            if (File.Exists(iconPath)) shortcut.IconLocation = iconPath + ",0";
            shortcut.Save();
        }
        finally { if (Marshal.IsComObject(shell)) Marshal.FinalReleaseComObject(shell); }
    }
}

internal static class InstallerBootstrap
{
    [STAThread]
    private static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new InstallerForm());
    }
}
