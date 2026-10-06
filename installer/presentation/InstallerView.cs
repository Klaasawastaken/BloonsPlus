using System;
using System.Drawing;
using System.Windows.Forms;
using System.Collections.Generic;
using System.Reflection;
using System.Drawing.Drawing2D;

internal sealed class InstallerStatusLabel : Label {
    public void SetObservedStatus(string text) {
        Text = text;
        string name = "Setup status: " + text;
        if (AccessibleName == name) return;
        AccessibleName = name;
        if (IsHandleCreated) AccessibilityNotifyClients(AccessibleEvents.NameChange, -1);
    }
}

internal sealed class InstallerView : UserControl {
    private readonly Label heading = new Label(), caption = new Label();
    private readonly Label footerNote = Copy("Internet needed for downloads. Sign in directly through Steam.",8,false);
    private readonly InstallerStatusLabel status = new InstallerStatusLabel();
    private readonly Button primary = new Button(), secondary = new Button();
    private readonly LinkLabel optionsLink = new LinkLabel(), detailsLink = new LinkLabel();
    private readonly Panel body = new Panel();
    private readonly FlowLayoutPanel content = new FlowLayoutPanel(), optionsPanel = new FlowLayoutPanel(), detailsPanel = new FlowLayoutPanel();
    private readonly ProgressBar progress = new ProgressBar();
    private readonly TextBox location = new TextBox(), iso = new TextBox(), details = new TextBox();
    private readonly CheckBox launch = new CheckBox(), desktop = new CheckBox(), startMenu = new CheckBox(), vm = new CheckBox();
    private readonly Queue<string> recent = new Queue<string>();
    private InstallerViewState state = InstallerViewState.Welcome();
    private bool optionsExpanded;
    private bool busy;
    private string lastSnapshotError;
    private string lastDetail;
    private readonly Button uninstall = QuietButton("Uninstall app files…");
    private readonly Button modify = QuietButton("Apply options");
    private Color gradientTop, gradientBottom;
    public event Action<string> CommandRequested;
    public string PrimaryText { get { return primary.Text; } }
    public Rectangle PrimaryBounds { get { return RectangleToClient(primary.RectangleToScreen(primary.ClientRectangle)); } }
    public bool OptionsExpanded { get { return optionsExpanded; } }
    public bool LaunchChecked { get { return launch.Checked; } set { launch.Checked = value; } }
    public Button PrimaryButton { get { return primary; } }
    public string SelectedRoot { get { return location.Text.Trim(); } }
    public string SelectedIso { get { return iso.Text.Trim(); } }
    public bool RequestedVm { get { return vm.Checked; } }
    public bool StartMenuChecked { get { return startMenu.Checked; } }
    public bool DesktopChecked { get { return desktop.Checked; } }
    public InstallerView(InstallerOptions options) {
        SuspendLayout(); AutoScaleMode = AutoScaleMode.Dpi;
        Font = new Font("Segoe UI", 10); Padding = new Padding(28); DoubleBuffered = true;
        var layout = new TableLayoutPanel { Dock=DockStyle.Fill,ColumnCount=1,RowCount=3 };
        layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize)); layout.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize)); Controls.Add(layout);
        var header = new TableLayoutPanel { Dock=DockStyle.Top,AutoSize=true,ColumnCount=2,Margin=new Padding(0,0,0,22) };
        header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100)); header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,64));
        var copy = Column(); copy.Dock=DockStyle.Fill;
        copy.Controls.Add(Copy("BLOONS+  /  SETUP",9,true));
        heading.Font=new Font("Segoe UI Semibold",24,FontStyle.Bold);heading.AutoSize=true;heading.Margin=new Padding(0,10,0,4);copy.Controls.Add(heading);
        var logo=new PictureBox {Width=56,Height=56,SizeMode=PictureBoxSizeMode.Zoom,Margin=new Padding(8,8,0,0)};
        using(var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream("BloonsPlus.Engineer")) {
            if(stream!=null) using(var art=Image.FromStream(stream))logo.Image=new Bitmap(art);
        }
        header.Controls.Add(copy,0,0);header.Controls.Add(logo,1,0);layout.Controls.Add(header,0,0);
        body.Dock=DockStyle.Fill;body.AutoScroll=true;body.Margin=Padding.Empty;layout.Controls.Add(body,0,1);
        content.FlowDirection=FlowDirection.TopDown;content.WrapContents=false;content.AutoSize=true;
        content.AutoSizeMode=AutoSizeMode.GrowAndShrink;content.Dock=DockStyle.Top;body.Controls.Add(content);
        status.AutoSize=true;status.Margin=new Padding(0,0,0,20);content.Controls.Add(status);
        progress.Width=550;progress.Height=9;progress.MarqueeAnimationSpeed=30;progress.Margin=new Padding(0,0,0,10);content.Controls.Add(progress);
        caption.AutoSize=true;caption.Font=new Font("Segoe UI",9);caption.Margin=new Padding(0,0,0,18);content.Controls.Add(caption);
        optionsLink.Text="Options";optionsLink.AutoSize=true;optionsLink.Margin=new Padding(0,0,0,12);optionsLink.LinkClicked+=delegate {ToggleOptions();};content.Controls.Add(optionsLink);
        optionsPanel.FlowDirection=FlowDirection.TopDown;optionsPanel.WrapContents=false;optionsPanel.AutoSize=true;optionsPanel.AutoSizeMode=AutoSizeMode.GrowAndShrink;
        optionsPanel.Controls.Add(Copy("Installation folder",9,true));location.Text=options.InstallRoot;location.Width=520;optionsPanel.Controls.Add(location);
        var chooseFolder=QuietButton("Change folder…");chooseFolder.Click+=delegate {using(var picker=new FolderBrowserDialog()) {picker.SelectedPath=SelectedRoot;if(picker.ShowDialog(FindForm())==DialogResult.OK)location.Text=picker.SelectedPath;}};optionsPanel.Controls.Add(chooseFolder);
        Check(desktop,"Desktop shortcut",options.DesktopShortcut);Check(startMenu,"Start menu shortcut",options.StartMenuShortcut);
        Check(launch,"Launch when setup completes",options.LaunchAfterInstall);Check(vm,"Set up the VM and game environment",options.RequestedVmSetup);
        optionsPanel.Controls.Add(desktop);optionsPanel.Controls.Add(startMenu);optionsPanel.Controls.Add(launch);optionsPanel.Controls.Add(vm);
        var isoToggle=QuietButton("Use an existing Windows 11 ISO…");
        iso.Text=options.RequestedIsoPath;iso.Width=520;iso.Visible=false;
        isoToggle.Click+=delegate {iso.Visible=!iso.Visible;ResizeContent();};optionsPanel.Controls.Add(isoToggle);optionsPanel.Controls.Add(iso);
        vm.CheckedChanged+=delegate {isoToggle.Enabled=iso.Enabled=vm.Checked;};
        optionsPanel.Controls.Add(Copy("Leave VM setup off to install the app now and connect your game later.",9,false));
        uninstall.Visible=false;uninstall.Click+=delegate {Emit("uninstall");};optionsPanel.Controls.Add(uninstall);
        modify.Visible=false;modify.Click+=delegate {Emit("modify");};optionsPanel.Controls.Add(modify);
        optionsPanel.Visible=false;content.Controls.Add(optionsPanel);
        detailsLink.Text="Show details";detailsLink.AutoSize=true;detailsLink.Margin=new Padding(0,10,0,12);detailsLink.LinkClicked+=delegate {ToggleDetails();};content.Controls.Add(detailsLink);
        detailsPanel.FlowDirection=FlowDirection.TopDown;detailsPanel.WrapContents=false;detailsPanel.AutoSize=true;detailsPanel.AutoSizeMode=AutoSizeMode.GrowAndShrink;
        details.Multiline=true;details.ReadOnly=true;details.ScrollBars=ScrollBars.Vertical;details.Width=520;details.Height=130;details.Font=new Font("Consolas",9);detailsPanel.Controls.Add(details);
        var detailActions=new FlowLayoutPanel {AutoSize=true};var copyDetails=QuietButton("Copy redacted details");var export=QuietButton("Export…");
        copyDetails.Click+=delegate {try {Clipboard.SetText(SharedDetails());} catch {caption.Text="Clipboard unavailable. Export details instead.";}};
        export.Click+=delegate {try {using(var picker=new SaveFileDialog()) {picker.FileName="BloonsPlus-setup-details.txt";picker.Filter="Text file (*.txt)|*.txt";if(picker.ShowDialog(FindForm())==DialogResult.OK)System.IO.File.WriteAllText(picker.FileName,SharedDetails());}} catch {caption.Text="Export failed. Choose a writable folder and try again.";}};
        detailActions.Controls.Add(copyDetails);detailActions.Controls.Add(export);detailsPanel.Controls.Add(detailActions);detailsPanel.Visible=false;content.Controls.Add(detailsPanel);
        var footer=new TableLayoutPanel {Dock=DockStyle.Fill,AutoSize=true,AutoSizeMode=AutoSizeMode.GrowAndShrink,ColumnCount=2,RowCount=2,Margin=new Padding(0,18,0,0)};
        footer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,42));footer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,58));
        footer.RowStyles.Add(new RowStyle(SizeType.AutoSize));footer.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        ConfigureButton(primary);ConfigureButton(secondary);primary.AutoSize=secondary.AutoSize=true;primary.Dock=secondary.Dock=DockStyle.Fill;
        primary.Click+=delegate {Emit(state.PrimaryAction);};secondary.Click+=delegate {if(state.SecondaryAction=="options")ToggleOptions();else if(state.SecondaryAction=="details")ToggleDetails();else Emit(state.SecondaryAction);};
        footer.Controls.Add(secondary,0,0);footer.Controls.Add(primary,1,0);
        footerNote.Margin=new Padding(0,10,0,0);footer.Controls.Add(footerNote,0,1);footer.SetColumnSpan(footerNote,2);layout.Controls.Add(footer,0,2);
        primary.TabIndex=0;secondary.TabIndex=1;optionsLink.TabIndex=2;detailsLink.TabIndex=3;
        status.AccessibleName="Setup status";progress.AccessibleName="Current step progress";
        location.AccessibleName="Installation folder";iso.AccessibleName="Existing Windows 11 ISO";details.AccessibleName="Recent setup details";
        ApplyTheme(false);ApplyState();Resize+=delegate {ResizeContent();};ResumeLayout(true);ResizeContent();
    }
    private static FlowLayoutPanel Column() {return new FlowLayoutPanel {FlowDirection=FlowDirection.TopDown,WrapContents=false,AutoSize=true,AutoSizeMode=AutoSizeMode.GrowAndShrink};}
    private static Label Copy(string text,float size,bool bold) {return new Label {Text=text,AutoSize=true,Font=new Font("Segoe UI",size,bold?FontStyle.Bold:FontStyle.Regular),Margin=new Padding(0,6,0,6)};}
    private static void Check(CheckBox control,string text,bool value) {control.Text=text;control.Checked=value;control.AutoSize=true;control.Margin=new Padding(0,6,0,6);}
    private static void ConfigureButton(Button button) {button.FlatStyle=FlatStyle.Flat;button.FlatAppearance.BorderSize=0;button.Font=new Font("Segoe UI Semibold",10,FontStyle.Bold);button.MinimumSize=new Size(130,38);button.Margin=new Padding(0,0,8,0);button.Cursor=Cursors.Hand;}
    private static Button QuietButton(string text) {var button=new Button {Text=text,AutoSize=true,Margin=new Padding(0,6,8,6)};ConfigureButton(button);return button;}
    private void Emit(string command) {var handler=CommandRequested;if(command!=null&&handler!=null)handler(command);}
    public void ToggleOptions() {optionsExpanded=!optionsExpanded;optionsPanel.Visible=optionsExpanded;optionsLink.Text=optionsExpanded?"Hide options":"Options";ResizeContent();}
    public void ToggleDetails() {detailsPanel.Visible=!detailsPanel.Visible;detailsLink.Text=detailsPanel.Visible?"Hide details":"Show details";ResizeContent();}
    public void Render(InstallerSnapshot snapshot) {
        string error = snapshot == null ? null : snapshot.Error;
        if (!String.IsNullOrWhiteSpace(error) && error != lastSnapshotError) AddDetail(error);
        lastSnapshotError = error;
        state=InstallerViewState.FromSnapshot(snapshot);ApplyState();
    }
    public void Welcome(string version,bool healthy,bool newer) {state=InstallerViewState.Welcome(version,healthy,newer);uninstall.Visible=modify.Visible=version!=null;ApplyState();}
    public void SetBusy(bool value) {busy=value;optionsPanel.Enabled=!busy;primary.Enabled=!busy&&state.PrimaryEnabled;}
    public void AddDetail(string line) {
        if (String.IsNullOrWhiteSpace(line) || line == lastDetail) return;
        lastDetail = line;
        recent.Enqueue(line.Length>4096?line.Substring(0,4096):line);while(recent.Count>100)recent.Dequeue();details.Text=String.Join(Environment.NewLine,recent.ToArray());
    }
    public string SharedDetails() {return InstallerDiagnostics.Redact(String.Join(Environment.NewLine,recent.ToArray()));}
    private void ApplyState() {
        if (state.ShowDetails) detailsPanel.Visible = true;
        detailsLink.Text = detailsPanel.Visible ? "Hide details" : "Show details";
        heading.Text=state.Heading;status.SetObservedStatus(state.Status);primary.Text=state.PrimaryText??"Setting up…";primary.Enabled=!busy&&state.PrimaryEnabled;
        secondary.Text=state.SecondaryText;secondary.Enabled=state.SecondaryAction!=null;
        progress.Visible=caption.Visible=state.ShowProgress;progress.Style=state.Animate?ProgressBarStyle.Marquee:ProgressBarStyle.Continuous;
        progress.Value=state.StagePercent.GetValueOrDefault();caption.Text=state.StagePercent.HasValue?"Current step · "+state.StagePercent+"%":state.Animate?"Working · progress is not measurable for this step":"Completed work is retained";
        progress.AccessibleDescription=caption.Text;
        optionsLink.Visible=!state.ShowProgress&&state.SecondaryAction!="options";
        detailsLink.Visible=(state.ShowProgress||recent.Count>0)&&state.SecondaryAction!="details";ResizeContent();
    }
    private void ResizeContent() {
        int width=Math.Max(260,body.ClientSize.Width-SystemInformation.VerticalScrollBarWidth-4);
        foreach(var label in new[]{heading,status,caption})label.MaximumSize=new Size(width,0);
        footerNote.MaximumSize=new Size(Math.Max(1,ClientSize.Width-Padding.Horizontal),0);
        progress.Width=location.Width=iso.Width=details.Width=width;
        foreach(Control container in new[]{optionsPanel,detailsPanel})foreach(Control child in container.Controls)if(child is Label)child.MaximumSize=new Size(width,0);
        content.PerformLayout();
    }
    public void ApplyTheme(bool dark) {
        Color background=ColorTranslator.FromHtml(dark?BrandTokens.DarkBackground:BrandTokens.LightBackground);
        Color text=ColorTranslator.FromHtml(dark?BrandTokens.DarkText:BrandTokens.LightText);
        Color soft=ColorTranslator.FromHtml(dark?BrandTokens.DarkSoft:BrandTokens.LightSoft);
        Color muted=ColorTranslator.FromHtml(dark?BrandTokens.DarkMuted:BrandTokens.LightMuted);
        if(SystemInformation.HighContrast){background=SystemColors.Window;text=SystemColors.WindowText;soft=SystemColors.Control;muted=text;}
        PaintControls(this,background,text,soft);status.ForeColor=caption.ForeColor=muted;
        gradientTop=background;gradientBottom=soft;
        if(SystemInformation.HighContrast)gradientBottom=gradientTop;
        primary.BackColor=ColorTranslator.FromHtml(BrandTokens.LightPrimary);primary.ForeColor=Color.White;
        if(SystemInformation.HighContrast){primary.BackColor=SystemColors.Highlight;primary.ForeColor=SystemColors.HighlightText;}
        optionsLink.LinkColor=detailsLink.LinkColor=SystemInformation.HighContrast?SystemColors.HotTrack:dark?Color.FromArgb(173,191,255):ColorTranslator.FromHtml(BrandTokens.LightPrimary);
        Invalidate(true);
    }
    private static void PaintControls(Control control,Color background,Color text,Color soft) {
        control.BackColor=control is TextBox||control is Button?soft:background;control.ForeColor=text;
        foreach(Control child in control.Controls)PaintControls(child,background,text,soft);
    }
    protected override void OnPaintBackground(PaintEventArgs args) {
        if(ClientSize.Width<=0||ClientSize.Height<=0)return;
        using(var brush=new LinearGradientBrush(ClientRectangle,gradientTop,gradientBottom,55f))args.Graphics.FillRectangle(brush,ClientRectangle);
    }
}
