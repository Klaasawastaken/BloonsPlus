import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerViewTests(unittest.TestCase):
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
