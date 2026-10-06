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
using System.Collections.Generic;
using System.Web.Script.Serialization;

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
    private readonly InstallerProgress progressState = new InstallerProgress();
    private readonly System.Windows.Forms.Timer progressTimer = new System.Windows.Forms.Timer();
    private int busyOffset;
    private bool requestedVmSetup = true;
    private string requestedIsoPath = "";
    private InstallerEngine activeEngine;
    private bool environmentPending;
    private readonly bool silent = Environment.GetCommandLineArgs().Any(arg => String.Equals(arg, "/silent", StringComparison.OrdinalIgnoreCase));
    private readonly string installRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Bloons+");
    private readonly string dataRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "BloonsPlus");
    private readonly string attemptToken = Environment.GetCommandLineArgs()
        .Where(arg => arg.StartsWith("/attempt:", StringComparison.OrdinalIgnoreCase))
        .Select(arg => arg.Substring(9)).FirstOrDefault();

    public InstallerForm()
    {
        Text = "Bloons+ Setup";
        try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }
        Width = 650;
        Height = 420;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = true;
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Color.FromArgb(237, 242, 251);

        var brand = new Panel { Left = 0, Top = 0, Width = 650, Height = 92, BackColor = Color.FromArgb(30, 42, 82) };
        var logo = new PictureBox { Left = 28, Top = 18, Width = 54, Height = 54,
            SizeMode = PictureBoxSizeMode.Zoom, BackColor = Color.Transparent };
        if (Icon != null) logo.Image = Icon.ToBitmap();
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
        ClientSize = new Size(900, 640);
        Font = new Font("Segoe UI", 10);
        ForeColor = Color.FromArgb(37, 61, 54);
        introduction.Text = "Your next run starts here.";
        introduction.SetBounds(320, 52, 535, 48);
        introduction.Font = new Font("Segoe UI Semibold", 23, FontStyle.Bold);
        introduction.BackColor = Color.Transparent;
        introduction.ForeColor = Color.FromArgb(37, 61, 54);
        AddCopy("Install once. Let guided setup handle the next steps.", 322, 110, 505, 34, 11, false);
        AddCopy("Bloons+", 50, 67, 196, 44, 27, true);
        AddCopy("LESS BUSYWORK. MORE PLAY.", 51, 110, 195, 24, 8, true);
        AddCopy("01  App & runtime", 50, 195, 215, 32, 12, true);
        AddCopy("Python and required components\nare checked automatically.", 50, 230, 207, 40, 9, false);
        AddCopy("02  Your game space", 50, 295, 215, 32, 12, true);
        AddCopy("Guided Windows VM setup\ncontinues in the app.", 50, 330, 207, 40, 9, false);
        AddCopy("03  Connect & play", 50, 395, 215, 32, 12, true);
        AddCopy("Sign in to Steam in the VM,\nthen install your owned game.", 50, 430, 207, 40, 9, false);
        AddCopy("MADE FOR YOUR DESKTOP", 50, 534, 218, 22, 8, true);
        AddCopy("MAKE IT YOURS", 329, 167, 450, 24, 9, true);
        vmSetup.SetBounds(329, 207, 450, 31);
        vmSetup.Text = "Continue with guided VM setup";
        vmSetup.BackColor = Color.FromArgb(245, 248, 244);
        isoLabel.Text = "Windows 11 ISO · optional";
        isoLabel.SetBounds(329, 258, 440, 25);
        isoLabel.BackColor = vmSetup.BackColor;
        isoPath.SetBounds(329, 291, 328, 30);
        isoPath.BorderStyle = BorderStyle.FixedSingle;
        browseIso.SetBounds(673, 285, 106, 40);
        StyleButton(browseIso, false);
        AddCopy("Leave empty to download Windows during guided setup.", 329, 339, 454, 27, 9, false);
        status.SetBounds(329, 409, 447, 48);
        status.BackColor = Color.FromArgb(245, 248, 244);
        status.Font = new Font("Segoe UI", 10);
        progress.SetBounds(329, 470, 447, 8);
        progress.Visible = false;
        progressCaption.SetBounds(329, 489, 447, 25);
        progressCaption.Text = "Ready · Internet needed for dependencies";
        progressCaption.Font = new Font("Segoe UI", 9);
        progressCaption.ForeColor = Color.FromArgb(112, 129, 119);
        progressCaption.BackColor = Color.Transparent;
        Controls.Add(progressCaption);
        progressTimer.Interval = 100;
        progressTimer.Tick += delegate {
            busyOffset = (busyOffset + 12) % 447;
            Invalidate(new Rectangle(329, 470, 447, 8));
        };
        FormClosed += delegate { progressTimer.Dispose(); };
        installButton.SetBounds(594, 565, 245, 47);
        StyleButton(installButton, true);
        AcceptButton = installButton;
        AddCopy("Your existing progress stays saved.", 322, 576, 263, 25, 9, false);
    }

    private void AddCopy(string text, int x, int y, int width, int height, float size, bool bold)
    {
        Controls.Add(new Label { Text = text, Left = x, Top = y, Width = width, Height = height,
            UseMnemonic = false,
            BackColor = Color.Transparent, ForeColor = bold ? Color.FromArgb(37, 61, 54) : Color.FromArgb(112, 129, 119),
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
        button.BackColor = primary ? Color.FromArgb(37, 61, 54) : Color.FromArgb(225, 235, 226);
        button.ForeColor = primary ? Color.White : Color.FromArgb(58, 86, 72);
        button.Font = new Font("Segoe UI", 10, FontStyle.Bold);
        button.Cursor = Cursors.Hand;
        using (var p = Rounded(new Rectangle(0, 0, button.Width, button.Height), 12)) button.Region = new Region(p);
    }

    protected override void OnPaintBackground(PaintEventArgs e)
    {
        using (var bg = new LinearGradientBrush(ClientRectangle, Color.FromArgb(246, 233, 224), Color.FromArgb(224, 239, 230), 35f))
            e.Graphics.FillRectangle(bg, ClientRectangle);
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        using (var accent = new SolidBrush(Color.FromArgb(239, 152, 126))) e.Graphics.FillEllipse(accent, 234, 62, 35, 35);
        using (var white = new Pen(Color.White, 3)) {
            e.Graphics.DrawLine(white, 244, 79, 258, 79);
            e.Graphics.DrawLine(white, 251, 72, 251, 86);
        }
        foreach (var rect in new[] { new Rectangle(24, 24, 268, 592), new Rectangle(306, 155, 550, 230), new Rectangle(306, 402, 550, 130) })
        {
            using (var shadow = Rounded(new Rectangle(rect.X, rect.Y+5, rect.Width, rect.Height), 22))
            using (var brush = new SolidBrush(Color.FromArgb(12, 53, 76, 112))) e.Graphics.FillPath(brush, shadow);
            using (var shape = Rounded(rect, 22))
            using (var fill = new SolidBrush(Color.FromArgb(155, 255, 255, 255)))
            using (var border = new Pen(Color.FromArgb(220, 255, 255, 255)))
            { e.Graphics.FillPath(fill, shape); e.Graphics.DrawPath(border, shape); }
        }
        using (var track = Rounded(new Rectangle(329, 470, 447, 8), 4))
        using (var brush = new SolidBrush(Color.FromArgb(217, 229, 219))) e.Graphics.FillPath(brush, track);
        if (progressState.IsBusy && progressTimer.Enabled) {
            using (var clip = Rounded(new Rectangle(329, 470, 447, 8), 4)) {
                GraphicsState saved = e.Graphics.Save();
                e.Graphics.SetClip(clip);
                using (var brush = new SolidBrush(Color.FromArgb(118, 170, 140))) {
                    e.Graphics.FillRectangle(brush, 329 + busyOffset - 90, 470, 90, 8);
                    e.Graphics.FillRectangle(brush, 329 + busyOffset + 357, 470, 90, 8);
                }
                e.Graphics.Restore(saved);
            }
            return;
        }
        int width = (int)(447L * progress.Value / 1000);
        if (width >= 8) using (var fill = Rounded(new Rectangle(329, 470, width, 8), 4))
        using (var brush = new LinearGradientBrush(new Rectangle(329, 470, 447, 8), Color.FromArgb(118,170,140), Color.FromArgb(239,152,126), 0f)) e.Graphics.FillPath(brush, fill);
    }

    private void SetStatus(string text, InstallerStage stage, int? percent = null, string scope = null)
    {
        if (IsDisposed) return;
        BeginInvoke((Action)delegate
        {
            status.Text = text;
            progressState.Update(stage, percent, scope);
            progress.Value = progressState.Value;
            progressCaption.Text = progressState.Caption;
            progressTimer.Enabled = progressState.IsBusy && !silent;
            Invalidate();
        });
    }

    private void SetDetail(string text)
    {
        if (!IsDisposed) BeginInvoke((Action)delegate { status.Text = text; });
    }

    private void SetFailure(string text)
    {
        if (!IsDisposed) BeginInvoke((Action)delegate {
            status.Text = text;
            progressState.Fail();
            progressTimer.Stop();
            progressCaption.Text = progressState.Caption;
            Invalidate();
        });
    }

    private void Install()
    {
        var options = new InstallerOptions(installRoot, dataRoot, Application.ExecutablePath, silent, attemptToken) {
            RequestedVmSetup = requestedVmSetup, RequestedIsoPath = requestedIsoPath
        };
        if (!environmentPending) {
        activeEngine = new InstallerEngine(options, new WindowsInstallerOperations(options));
        activeEngine.ProgressChanged += delegate(InstallerProgress state) {
            if (state.Failed) SetFailure(state.Message);
            else SetStatus(state.Message, state.Stage, state.Percent, state.Scope);
        };
        activeEngine.DetailAdded += SetDetail;
        }
        var result = (environmentPending ? activeEngine.ResumeEnvironmentAsync(System.Threading.CancellationToken.None)
            : activeEngine.RunAsync(System.Threading.CancellationToken.None)).GetAwaiter().GetResult();
        if (result.LocalReady) {
            if (!silent && requestedVmSetup && !result.EnvironmentReady) {
                environmentPending = true;
                if (!IsDisposed) BeginInvoke((Action)delegate {
                    progressTimer.Stop();
                    status.Text = activeEngine.CurrentSnapshot.Status;
                    installButton.Text = result.RestartRequired ? "Continue after restart" : "Continue setup";
                    installButton.Enabled = true;
                    progressCaption.Text = "App installed · environment setup needs attention";
                });
                return;
            }
            Task.Delay(1800).ContinueWith(delegate { if (!IsDisposed) BeginInvoke((Action)Close); });
            return;
        }
        if (silent) {
            Environment.ExitCode = result.ExitCode;
            if (!IsDisposed && IsHandleCreated) BeginInvoke((Action)Close);
            return;
        }
        if (!IsDisposed && IsHandleCreated) BeginInvoke((Action)delegate {
            installButton.Enabled = vmSetup.Enabled = true;
            isoPath.Enabled = browseIso.Enabled = vmSetup.Checked;
            installButton.Text = "Retry installation";
            MessageBox.Show(this, "Setup paused. You can change your options and retry.\r\n\r\n" + result.Error + "\r\n\r\nDiagnostic log: " + options.LogPath,
                "Bloons+ Setup", MessageBoxButtons.OK, MessageBoxIcon.Error);
        });
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
