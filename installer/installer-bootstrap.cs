using System;
using System.IO;
using System.Linq;
using System.Drawing;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using Microsoft.Win32;

// Form events adapt the native engine; installation work runs outside the UI thread.
internal sealed class InstallerForm : Form {
    private readonly InstallerView view;
    private readonly System.Windows.Forms.Timer refresh = new System.Windows.Forms.Timer();
    private readonly bool silent = Environment.GetCommandLineArgs().Any(x => String.Equals(x,"/silent",StringComparison.OrdinalIgnoreCase));
    private readonly string dataRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"BloonsPlus");
    private readonly string attempt;
    private InstallerEngine engine;
    private InstallerOptions options;
    private InstallerSnapshot pending;
    private CancellationTokenSource cancellation;
    private bool working, environmentPending, closeAfterPause, commandPending;
    private string operation="install";
    public InstallerForm() {
        Text="Bloons+ Setup";ClientSize=new Size(640,540);MinimumSize=new Size(600,480);
        StartPosition=FormStartPosition.CenterScreen;AutoScaleMode=AutoScaleMode.Dpi;
        try {Icon=Icon.ExtractAssociatedIcon(Application.ExecutablePath);}catch{}
        attempt=Environment.GetCommandLineArgs().Where(x=>x.StartsWith("/attempt:",StringComparison.OrdinalIgnoreCase)).Select(x=>x.Substring(9)).FirstOrDefault();
        options=new InstallerOptions(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Programs","Bloons+"),dataRoot,Application.ExecutablePath,silent,attempt);
        options=InstallerPreferences.Load(options);
        view=new InstallerView(options){Dock=DockStyle.Fill};Controls.Add(view);AcceptButton=view.PrimaryButton;
        bool dark=false;try {using(var key=Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"))dark=key!=null&&Convert.ToInt32(key.GetValue("AppsUseLightTheme",1))==0;}catch{}
        view.ApplyTheme(dark);view.CommandRequested+=HandleCommand;
        refresh.Interval=100;refresh.Tick+=delegate {var snapshot=Interlocked.Exchange(ref pending,null);if(snapshot!=null)view.Render(snapshot);};refresh.Start();
        FormClosing+=delegate(object sender,FormClosingEventArgs args) {
            if(!working||cancellation==null)return;
            if(MessageBox.Show(this,"Pause setup after its current safe step? Active installers and your replay will remain running.","Pause setup",MessageBoxButtons.YesNo,MessageBoxIcon.Question,MessageBoxDefaultButton.Button2)!=DialogResult.Yes){args.Cancel=true;return;}
            args.Cancel=true;closeAfterPause=true;cancellation.Cancel();
        };
        FormClosed+=delegate {refresh.Dispose();};
        if(silent){ShowInTaskbar=false;WindowState=FormWindowState.Minimized;Opacity=0;Shown+=async delegate {await Run(false);};}
        else Shown+=async delegate {await InspectInstalled();};
    }
    private async Task InspectInstalled() {
        working=true;view.SetBusy(true);
        try {
            var observation=await Task.Run(()=>InstallerInventory.Inspect(options.InstallRoot,InstallerInventory.CurrentFingerprint));
            bool runtime=false;
            if(observation.FilesHealthy)runtime=await Task.Run(()=>{using(var operations=new WindowsInstallerOperations(options))return operations.ProbeInstalledRuntime();});
            if(IsDisposed)return;
            if(observation.Exists)view.Welcome(observation.Version??"Unknown build",observation.FilesHealthy&&runtime,observation.DifferentBuild);
            if(runtime&&observation.FilesHealthy) {
                var saved=InstallSession.ReadExisting(options.InstallRoot);
                if(saved!=null&&saved.Phase!="complete"&&saved.EnvironmentRequired&&saved.AppValidated) {
                    environmentPending=true;CreateEngine();
                    saved.Phase="recovering";saved.HumanAction="retry";saved.Status="Saved setup found. Continue to check its current state.";view.Render(saved);
                }
            }
        } catch(Exception error){if(!IsDisposed){view.AddDetail(error.ToString());view.Welcome("Needs inspection",false,false);}}
        finally {working=false;if(!IsDisposed)view.SetBusy(false);}
    }
    private async void HandleCommand(string command) {
        if(command=="cancel"){if(cancellation!=null)cancellation.Cancel();return;}
        if(commandPending)return;commandPending=true;view.SetBusy(true);
        try {
            if(command=="close"){Close();return;}
            if(command=="launch"){using(var operations=new WindowsInstallerOperations(options))operations.LaunchApp();Close();return;}
            if(command=="uninstall") {
                if(working)return;
                if(MessageBox.Show(this,"Remove unchanged BloonsPlus app files? Your VM, game, saves, routes and personal settings stay. Modified files also stay.","Uninstall BloonsPlus",MessageBoxButtons.YesNo,MessageBoxIcon.Warning,MessageBoxDefaultButton.Button2)!=DialogResult.Yes)return;
                working=true;view.SetBusy(true);
                try {
                    await Task.Run(()=>{using(InstallerEngine.AcquireInstallLock(options.InstallRoot))using(var operations=new WindowsInstallerOperations(options)){operations.CloseInstalledControllers();InstallerInventory.RemoveUnchangedFiles(options.InstallRoot);}});
                    view.Welcome(null,false,false);view.AddDetail("App files removed. Personal data and the VM are retained.");
                } finally {working=false;view.SetBusy(false);}return;
            }
            if(command=="restart_later"||command=="restart_now"||command=="open_vm") {
                if(engine==null||engine.CurrentSnapshot==null)return;
                if(command=="restart_now"&&MessageBox.Show(this,"Restart Windows now? Save your work before continuing.","Restart required",MessageBoxButtons.YesNo,MessageBoxIcon.Question,MessageBoxDefaultButton.Button2)!=DialogResult.Yes)return;
                await engine.CommandEnvironmentAsync(command,CancellationToken.None);
                if(command=="restart_later")Close();return;
            }
            if(!working){operation=command=="update"?"update":command=="repair"||command=="modify"?"repair":"install";await Run(environmentPending);}
        }catch(Exception error){view.AddDetail(error.ToString());view.Render(new InstallerSnapshot{Phase="failed",Status="Setup needs attention. Open details and retry."});}
        finally {commandPending=false;if(!IsDisposed)view.SetBusy(working);}
    }
    private void CreateEngine() {
        engine=new InstallerEngine(options,new WindowsInstallerOperations(options));
        engine.SnapshotChanged+=snapshot=>Interlocked.Exchange(ref pending,snapshot);
        engine.DetailAdded+=line=>{if(!IsDisposed&&IsHandleCreated)BeginInvoke((Action)(()=>view.AddDetail(line)));};
    }
    private async Task Run(bool resume) {
        if(working)return;working=true;view.SetBusy(true);cancellation=new CancellationTokenSource();
        try {
            if(!resume) {
                string root=Path.GetFullPath(view.SelectedRoot);
                if(String.Equals(root.TrimEnd('\\'),Path.GetPathRoot(root).TrimEnd('\\'),StringComparison.OrdinalIgnoreCase)||File.Exists(root))throw new ArgumentException("Choose an app folder rather than a drive root or file.");
                string iso=view.SelectedIso;if(view.RequestedVm&&!String.IsNullOrWhiteSpace(iso)&&!File.Exists(iso))throw new FileNotFoundException("Choose an existing Windows ISO or leave the field empty.");
                options=new InstallerOptions(root,dataRoot,Application.ExecutablePath,silent,attempt){Operation=operation,RequestedVmSetup=!silent&&view.RequestedVm,RequestedIsoPath=iso,DesktopShortcut=view.DesktopChecked,StartMenuShortcut=view.StartMenuChecked,LaunchAfterInstall=view.LaunchChecked};
                CreateEngine();
            }
            var result=await(resume?engine.ResumeEnvironmentAsync(cancellation.Token):engine.RunAsync(cancellation.Token));
            environmentPending=result.LocalReady&&options.RequestedVmSetup&&!result.EnvironmentReady;
            Interlocked.Exchange(ref pending,null);if(engine.CurrentSnapshot!=null)view.Render(engine.CurrentSnapshot);
            if(!String.IsNullOrEmpty(result.Error))view.AddDetail(result.Error);
            if(silent){Environment.ExitCode=result.ExitCode;working=false;Close();}
        }catch(Exception error){view.AddDetail(error.ToString());view.Render(new InstallerSnapshot{Phase=error is OperationCanceledException?"cancelled":"failed",Status="Setup paused. Completed work is retained. Open details to continue."});}
        finally {working=false;view.SetBusy(false);cancellation.Dispose();cancellation=null;if(closeAfterPause)Close();}
    }
}
internal static class InstallerBootstrap {
    [DllImport("user32.dll")]private static extern bool SetProcessDpiAwarenessContext(IntPtr value);
    [DllImport("shell32.dll",CharSet=CharSet.Unicode)]private static extern int SetCurrentProcessExplicitAppUserModelID(string value);
    [STAThread]private static void Main() {
        try {SetProcessDpiAwarenessContext(new IntPtr(-4));}catch(EntryPointNotFoundException){}
        SetCurrentProcessExplicitAppUserModelID("com.bloonsplus.setup");
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new InstallerForm());
    }
}
