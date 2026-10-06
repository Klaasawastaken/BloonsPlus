import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerViewTests(unittest.TestCase):
    def test_native_accessible_status_and_progress_expose_current_observation(self):
        """Read actual native accessibility objects and own-window name events."""
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'ViewAccessibilityChecks.cs'
            source.write_text(r'''
using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;
internal sealed class AccessibilityOffscreenForm : Form {
 protected override bool ShowWithoutActivation {get{return true;}}
 protected override CreateParams CreateParams {get{var value=base.CreateParams;value.ExStyle|=0x08000000|0x80;return value;}}
}
internal static class ViewAccessibilityChecks {
 delegate void WinEvent(IntPtr hook,uint type,IntPtr window,int obj,int child,uint thread,uint time);
 [DllImport("user32.dll")] static extern IntPtr SetWinEventHook(uint min,uint max,IntPtr module,WinEvent callback,uint process,uint thread,uint flags);
 [DllImport("user32.dll")] static extern bool UnhookWinEvent(IntPtr hook);
 static void Check(bool value,string why) {if(!value)throw new Exception(why);}
 static Control Find(Control parent,string name) {
  if(parent.AccessibleName!=null&&parent.AccessibleName.StartsWith(name,StringComparison.Ordinal))return parent;
  foreach(Control child in parent.Controls){var found=Find(child,name);if(found!=null)return found;}
  return null;
 }
 static void Drain() {
  var watch=Stopwatch.StartNew();
  while(watch.ElapsedMilliseconds<100){Application.DoEvents();Thread.Sleep(5);}
 }
 [STAThread] static int Main(string[] args) {
  try {Run(args);return 0;} catch(Exception error){Console.Error.WriteLine(error);return 1;}
 }
 static void Run(string[] args) {
  Application.EnableVisualStyles();
  foreach(bool dark in new[]{false,true}) {
   using(var form=new AccessibilityOffscreenForm()) using(var view=new InstallerView(new InstallerOptions(Path.Combine(args[0],"app"),args[0],"unused.exe",false,null))) {
    form.ShowInTaskbar=false;form.StartPosition=FormStartPosition.Manual;form.Location=new Point(-10000,-10000);
    form.ClientSize=new Size(640,540);form.Controls.Add(view);view.Dock=DockStyle.Fill;view.ApplyTheme(dark);form.Show();form.PerformLayout();
    Check(form.Bounds.Right<0,"Fixture became visible on desktop");
    var status=Find(view,"Setup status");var progress=Find(view,"Current step progress");
    Check(status!=null&&progress!=null,"Status/progress accessibility targets absent");
    Check(status.AccessibilityObject.Name=="Setup status: Install BloonsPlus and connect your game in one guided setup.","Accessible welcome status hides its actual text");
    int announcements=0;
    WinEvent callback=delegate(IntPtr hook,uint type,IntPtr window,int obj,int child,uint thread,uint time){if(window==status.Handle&&obj==-4)announcements++;};
    // Scope the read-only event listener to this fixture process. No global input.
    var listener=SetWinEventHook(0x800c,0x800c,IntPtr.Zero,callback,(uint)Process.GetCurrentProcess().Id,0,0);
    Check(listener!=IntPtr.Zero,"Own-process accessibility event listener unavailable");
    try {
     var snapshot=new InstallerSnapshot{Phase="downloading",Status="Downloading required components",StageNumerator=10,StageDenominator=100};
     view.Render(snapshot);Drain();
     Check(status.AccessibilityObject.Name=="Setup status: Downloading required components","Download status not exposed");
     Check(announcements>0,"Changed status did not announce a native name event");
     Check(progress.AccessibilityObject.Description=="Current step · 10%","Measured progress description absent");
     int prior=announcements;
     snapshot.StageNumerator=20;view.Render(snapshot);Drain();
     Check(announcements==prior,"Progress-only observation repeated status announcement");
     Check(progress.AccessibilityObject.Description=="Current step · 20%","Measured progress description stale");
     snapshot.StageNumerator=snapshot.StageDenominator=null;snapshot.Indeterminate=true;view.Render(snapshot);Drain();
     Check(progress.AccessibilityObject.Description=="Working · progress is not measurable for this step","Unknown work exposed a false measured percentage");
     view.Render(new InstallerSnapshot{Phase="failed",Status="RuntimeError: user@127.0.0.1 permission denied",Error="Private fixture diagnostic"});Drain();
     Check(status.AccessibilityObject.Name=="Setup status: A setup component needs attention. Open details, then retry.","Accessible failure does not match friendly visible status");
     Check(announcements>prior,"Failure did not announce changed status");
     view.Render(new InstallerSnapshot{Phase="complete",AppValidated=true,EnvironmentRequired=false});Drain();
     Check(status.AccessibilityObject.Name=="Setup status: App installed — environment setup deferred.","Accessible completion invents environment readiness");
    } finally {UnhookWinEvent(listener);GC.KeepAlive(callback);}
   }
  }
 }
}
''', encoding='utf-8')
            binary = Path(folder) / 'ViewAccessibilityChecks.exe'
            compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
            files = [*sorted((root / 'installer/native').glob('*.cs')),
                     *sorted((root / 'installer/presentation').glob('*.cs')), source]
            result = subprocess.run([str(compiler), '/nologo', '/target:exe', '/main:ViewAccessibilityChecks',
                '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                '/reference:Accessibility.dll', '/reference:System.IO.Compression.dll',
                '/reference:Microsoft.CSharp.dll', '/reference:System.Web.Extensions.dll',
                '/out:' + str(binary), *map(str, files)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_native_keyboard_traversal_skips_hidden_and_busy_controls(self):
        """Exercise WinForms selection, not declared TabIndex values or OS input."""
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'ViewKeyboardChecks.cs'
            source.write_text(r'''
using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Collections.Generic;
internal sealed class KeyboardOffscreenForm : Form {
 protected override bool ShowWithoutActivation {get{return true;}}
 protected override CreateParams CreateParams {get{var value=base.CreateParams;value.ExStyle|=0x08000000|0x80;return value;}}
}
internal static class ViewKeyboardChecks {
 static void Check(bool value,string why) {if(!value)throw new Exception(why);}
 static string Name(Control control) {return control.AccessibleName??control.Text;}
 static Control Selected(ContainerControl parent) {
  Control selected=parent.ActiveControl;
  while(selected is ContainerControl && ((ContainerControl)selected).ActiveControl!=null)
   selected=((ContainerControl)selected).ActiveControl;
  return selected;
 }
 static List<Control> Traversal(InstallerView view,bool forward) {
  var result=new List<Control>();Control current=null;
  while((current=view.GetNextControl(current,forward))!=null) {
   if(current.CanSelect&&current.TabStop)result.Add(current);
   Check(result.Count<50,"Keyboard traversal did not terminate");
  }
  return result;
 }
 static void CheckSequence(Form form,InstallerView view,params string[] expected) {
  foreach(bool forward in new[]{true,false}) {
   var controls=Traversal(view,forward);
   Check(controls.Count==expected.Length,"Unexpected focusable control count: "+controls.Count);
   Control previous=null;
   for(int index=0;index<controls.Count;index++) {
    Check(Name(controls[index])==expected[forward?index:expected.Length-index-1],"Wrong keyboard order: "+Name(controls[index]));
    Check(form.SelectNextControl(previous,forward,true,true,false),"Native selection refused a reachable control");
    Check(Selected(form)==controls[index],"Native selection disagrees with declared traversal");
    Check(!String.IsNullOrWhiteSpace(controls[index].AccessibilityObject.Name),"Focusable control has no accessible name");
    Check(controls[index].AccessibilityObject.Role!=AccessibleRole.None,"Focusable control has no accessible role");
    previous=controls[index];
   }
   Check(form.SelectNextControl(previous,forward,true,true,true),"Keyboard wrap failed");
   Check(Selected(form)==controls[0],"Keyboard wrap selected a hidden or disabled control");
  }
 }
 [STAThread] static void Main(string[] args) {
  Application.EnableVisualStyles();
  foreach(bool dark in new[]{false,true}) {
   using(var form=new KeyboardOffscreenForm()) using(var view=new InstallerView(new InstallerOptions(Path.Combine(args[0],"app"),args[0],"unused.exe",false,null))) {
    form.ShowInTaskbar=false;form.StartPosition=FormStartPosition.Manual;form.Location=new Point(-10000,-10000);
    form.ClientSize=new Size(640,540);form.Controls.Add(view);view.Dock=DockStyle.Fill;view.ApplyTheme(dark);form.Show();form.PerformLayout();
    Check(form.Bounds.Right<0,"Fixture became visible on the desktop");
    CheckSequence(form,view,"Install BloonsPlus","Options");
    view.ToggleOptions();
    CheckSequence(form,view,"Installation folder","Change folder…","Desktop shortcut","Start menu shortcut",
     "Launch when setup completes","Set up the VM and game environment","Use an existing Windows 11 ISO…","Install BloonsPlus","Options");
    view.ToggleOptions();
    view.Render(new InstallerSnapshot{Phase="downloading",Status="Downloading components"});view.SetBusy(true);
    CheckSequence(form,view,"Show details","Pause setup");
    view.ToggleDetails();
    CheckSequence(form,view,"Hide details","Recent setup details","Copy redacted details","Export…","Pause setup");
    view.Render(new InstallerSnapshot{Phase="failed",Status="Setup needs attention",Error="Fixture failure"});view.SetBusy(false);
    CheckSequence(form,view,"Recent setup details","Copy redacted details","Export…","Continue setup","Show details");
    view.Render(new InstallerSnapshot{Phase="complete",AppValidated=true,EnvironmentRequired=true,EnvironmentValidated=true});
    Check(Traversal(view,true).Exists(control=>control==view.PrimaryButton),"Validated Launch is unreachable");
   }
  }
 }
}
''', encoding='utf-8')
            binary = Path(folder) / 'ViewKeyboardChecks.exe'
            compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
            files = [*sorted((root / 'installer/native').glob('*.cs')),
                     *sorted((root / 'installer/presentation').glob('*.cs')), source]
            result = subprocess.run([str(compiler), '/nologo', '/target:exe', '/main:ViewKeyboardChecks',
                '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                '/reference:Accessibility.dll', '/reference:System.IO.Compression.dll',
                '/reference:Microsoft.CSharp.dll', '/reference:System.Web.Extensions.dll',
                '/out:' + str(binary), *map(str, files)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_native_controls_render_offscreen_in_both_themes(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'ViewRenderChecks.cs'
            source.write_text(r'''
using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Collections.Generic;
internal sealed class OffscreenForm : Form {
 protected override bool ShowWithoutActivation {get{return true;}}
 protected override CreateParams CreateParams {get{var value=base.CreateParams;value.ExStyle|=0x08000000|0x80;return value;}}
}
internal static class ViewRenderChecks {
 static void Check(bool value,string message) { if(!value)throw new Exception(message); }
 [STAThread] static void Main(string[] args) {
  Application.EnableVisualStyles();
  for(int theme=0;theme<2;theme++) for(int scale=1;scale<=3;scale++) {
   float factor=scale==1?1f:scale==2?1.5f:2f;
   var options=new InstallerOptions(Path.Combine(args[0],"app"),args[0],"unused.exe",false,null);
   using(var form=new OffscreenForm()) using(var view=new InstallerView(options)) {
    form.ShowInTaskbar=false;form.StartPosition=FormStartPosition.Manual;form.Location=new Point(-10000,-10000);
    form.ClientSize=new Size(640,540);form.Controls.Add(view);view.Dock=DockStyle.Fill;
    view.ApplyTheme(theme==1);form.Show();form.PerformLayout();
    Check(form.Bounds.Right<0,"Fixture window became visible on the desktop");
    Check(view.PrimaryText=="Install BloonsPlus","Wrong initial action");
    Check(!view.OptionsExpanded,"Options visible on welcome");
    view.ToggleOptions();Check(view.OptionsExpanded,"Options cannot be opened");
    view.LaunchChecked=false;
    view.Render(new InstallerSnapshot {Phase="failed",Status="user@127.0.0.1: Permission denied"});
    var failedSnapshot=new InstallerSnapshot {Phase="failed",Status="Setup needs attention",Error="provision: Fixture capability failure"};
    view.Render(failedSnapshot);
    string failedDetails=view.SharedDetails();
    Check(failedDetails.Contains("Fixture capability failure"),"Failed snapshot left diagnostics empty");
    view.Render(failedSnapshot);Check(view.SharedDetails()==failedDetails,"Polling duplicated identical diagnostics");
    Check(!view.LaunchChecked,"Retry reset options");
    view.SetBusy(true);view.Render(new InstallerSnapshot{Phase="complete",AppValidated=true});
    Check(!view.PrimaryButton.Enabled,"Progress refresh re-enabled an active command");view.SetBusy(false);
    view.ToggleOptions();
    var fonts=new Dictionary<Control,Font>();RememberFonts(form,fonts);
    form.Scale(new SizeF(factor,factor));foreach(var pair in fonts)pair.Key.Font=new Font(pair.Value.FontFamily,pair.Value.Size*factor,pair.Value.Style);form.PerformLayout();
    foreach(string screen in new[]{"welcome","options","error","complete"}) {
     view.Welcome(null,false,false);
     if(view.OptionsExpanded)view.ToggleOptions();
     if(screen=="options")view.ToggleOptions();
     if(screen=="error")view.Render(new InstallerSnapshot{Phase="failed",Status="Setup needs attention"});
     if(screen=="complete")view.Render(new InstallerSnapshot{Phase="complete",AppValidated=true,EnvironmentRequired=true,EnvironmentValidated=true,StageNumerator=100,StageDenominator=100});
     form.PerformLayout();
     using(var bitmap=new Bitmap(form.ClientSize.Width,form.ClientSize.Height)) {
      view.DrawToBitmap(bitmap,new Rectangle(Point.Empty,bitmap.Size));
      bitmap.Save(Path.Combine(args[0],"installer-"+screen+"-"+(theme==1?"dark":"light")+"-"+(int)(factor*100)+".png"));
     }
    }
    Check(view.PrimaryBounds.Right<=view.ClientSize.Width && view.PrimaryBounds.Bottom<=view.ClientSize.Height,"Action clipped");
   }
  }
 }
 static void RememberFonts(Control control,Dictionary<Control,Font> fonts) {
  fonts[control]=control.Font;
  foreach(Control child in control.Controls)RememberFonts(child,fonts);
 }
}
''',encoding='utf-8')
            binary=Path(folder)/'ViewRenderChecks.exe'
            compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
            files=[*sorted((root/'installer/native').glob('*.cs')),*sorted((root/'installer/presentation').glob('*.cs')),source]
            compile=subprocess.run([str(compiler),'/nologo','/target:exe','/main:ViewRenderChecks',
                '/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.IO.Compression.dll',
                '/reference:Microsoft.CSharp.dll','/reference:System.Web.Extensions.dll',
                '/resource:'+str(root/'tower-icons/engineer-monkey.png')+',BloonsPlus.Engineer','/out:'+str(binary),*map(str,files)],capture_output=True,text=True)
            self.assertEqual(compile.returncode,0,compile.stdout+compile.stderr)
            artifacts=root/'.superpowers/sdd/2026-10-06-installer-startup/view-artifacts'
            artifacts.mkdir(parents=True,exist_ok=True)
            run=subprocess.run([str(binary),str(artifacts)],capture_output=True,text=True,timeout=40)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertEqual(len(list(artifacts.glob('installer-welcome-*.png'))),6)
            self.assertEqual(len(list(artifacts.glob('installer-options-*.png'))),6)

    def test_compact_states_validation_actions_and_redacted_details(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'ViewChecks', r'''
using System;
internal static class ViewChecks {
 static void Check(bool value,string message) { if(!value) throw new Exception(message); }
 static void Main() {
  var welcome=InstallerViewState.Welcome();
  Check(welcome.PrimaryAction=="start" && welcome.PrimaryText=="Install BloonsPlus","Welcome lacks one install action");
  Check(!welcome.ShowProgress && !welcome.ShowDetails && !welcome.ShowIso,"Welcome leaks pipeline details");
  var snapshot=new InstallerSnapshot {Phase="complete",AppValidated=true,EnvironmentRequired=true};
  Check(InstallerViewState.FromSnapshot(snapshot).PrimaryAction!="launch","Unvalidated environment offered Launch");
  snapshot.EnvironmentValidated=true;
  Check(InstallerViewState.FromSnapshot(snapshot).PrimaryAction=="launch","Validated completion did not offer Launch");
  snapshot.EnvironmentRequired=false;snapshot.EnvironmentValidated=false;
  Check(InstallerViewState.FromSnapshot(snapshot).Status.Contains("deferred"),"Explicit defer hidden");
  snapshot.Phase="restart_required";
  Check(InstallerViewState.FromSnapshot(snapshot).PrimaryAction=="restart_now","Restart action missing");
  Check(InstallerViewState.FromSnapshot(snapshot).SecondaryAction=="restart_later","Later action missing");
  snapshot.Phase="recovering";snapshot.HumanAction="wait_replay";
  Check(!InstallerViewState.FromSnapshot(snapshot).Animate,"Replay wait animated as work");
  snapshot.Phase="downloading";snapshot.HumanAction=null;snapshot.StageNumerator=42;snapshot.StageDenominator=100;
  Check(InstallerViewState.FromSnapshot(snapshot).StagePercent==42,"Measured progress missing");
  snapshot.StageNumerator=snapshot.StageDenominator=null;
  Check(InstallerViewState.FromSnapshot(snapshot).Animate,"Unknown active work not indeterminate");
  snapshot.Phase="failed";snapshot.Status="user@127.0.0.1: Permission denied (publickey)";
  var failed=InstallerViewState.FromSnapshot(snapshot);
  Check(failed.PrimaryAction=="retry"&&!failed.Status.Contains("user@"),"Raw SSH failure replaced friendly status");
  string raw="user@127.0.0.1 C:\\Users\\" + "fixture\\private\\file.json X-Bloons-Setup-Key: "+new string('a',64)+" session "+new string('b',32)+"\n-----BEGIN OPENSSH " + "PRIVATE KEY-----\nsecret-content\n-----END OPENSSH PRIVATE KEY-----";
  string redacted=InstallerDiagnostics.Redact(raw);
  Check(!redacted.Contains("secret-content")&&!redacted.Contains("fixture")&&!redacted.Contains("127.0.0.1")&&!redacted.Contains(new string('a',64))&&!redacted.Contains(new string('b',32)),"Shared details contain private information");
  Check(InstallerDiagnostics.Redact(new string('x',200000)).Length<=65536,"Details export unbounded");
 }
}
''')
            result = subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
