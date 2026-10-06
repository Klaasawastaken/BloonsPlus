"""Native text-only scaling checks; no desktop input or machine settings changes."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'Windows native controls')
class InstallerTextScaleTests(unittest.TestCase):
    def test_text_only_scaling_keeps_actions_and_copy_readable(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'TextScaleChecks.cs'
            source.write_text(r'''
using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Collections.Generic;
internal sealed class TextScaleOffscreenForm : Form {
 protected override bool ShowWithoutActivation {get{return true;}}
 protected override CreateParams CreateParams {get{var value=base.CreateParams;value.ExStyle|=0x08000000|0x80;return value;}}
}
internal static class TextScaleChecks {
 static void Check(bool value,string why){if(!value)throw new Exception(why);}
 static IEnumerable<Control> Leaves(Control parent){
  foreach(Control child in parent.Controls){
   if(child.Controls.Count==0)yield return child;
   else foreach(var leaf in Leaves(child))yield return leaf;
  }
 }
 static void ScaleText(Control parent,float factor){
  var fonts=new Dictionary<Control,Font>();Remember(parent,fonts);
  foreach(var pair in fonts)pair.Key.Font=new Font(pair.Value.FontFamily,pair.Value.Size*factor,pair.Value.Style);
 }
 static void Remember(Control control,Dictionary<Control,Font> fonts){
  fonts[control]=control.Font;foreach(Control child in control.Controls)Remember(child,fonts);
 }
 static void Readable(InstallerView view,string screen,float factor){
  foreach(var control in Leaves(view)){
   if(!control.Visible||String.IsNullOrWhiteSpace(control.Text)||control is TextBox)continue;
   string context=screen+" "+factor+" "+control.Text;
   if(control is Label||control is Button||control is CheckBox){
    var preferred=control.GetPreferredSize(new Size(control.ClientSize.Width,0));
    Check(preferred.Height<=control.Height,"Text height clipped: "+context+" height="+control.Height+" preferred="+preferred.Height+" width="+control.Width+" type="+control.GetType().Name);
    Check(control.Right<=control.Parent.ClientSize.Width,"Text extends beyond its parent: "+context);
   }
  }
  Check(view.PrimaryBounds.Right<=view.ClientSize.Width&&view.PrimaryBounds.Bottom<=view.ClientSize.Height,"Primary action outside window");
 }
 [STAThread] static int Main(string[] args){
  try{Run(args);return 0;}catch(Exception error){Console.Error.WriteLine(error);return 1;}
 }
 static void Run(string[] args){
  Application.EnableVisualStyles();
  foreach(bool dark in new[]{false,true})foreach(float factor in new[]{1f,1.25f,1.5f,2f})foreach(bool minimum in new[]{false,true}){
   using(var form=new TextScaleOffscreenForm())using(var view=new InstallerView(new InstallerOptions(Path.Combine(args[0],"app"),args[0],"unused.exe",false,null))){
    form.ShowInTaskbar=false;form.StartPosition=FormStartPosition.Manual;form.Location=new Point(-10000,-10000);
    form.ClientSize=new Size(640,540);form.MinimumSize=new Size(600,480);if(minimum)form.Size=form.MinimumSize;
    form.Controls.Add(view);view.Dock=DockStyle.Fill;view.ApplyTheme(dark);
    form.Show();ScaleText(view,factor);form.PerformLayout();Application.DoEvents();
    Check(form.Bounds.Right<0,"Fixture became visible on desktop");
    foreach(string screen in new[]{"welcome","options","downloading","failed","restart","complete"}){
     view.Welcome(null,false,false);if(view.OptionsExpanded)view.ToggleOptions();
     if(screen=="options")view.ToggleOptions();
     if(screen=="downloading")view.Render(new InstallerSnapshot{Phase="downloading",Status="Downloading required components",StageNumerator=42,StageDenominator=100});
     if(screen=="failed")view.Render(new InstallerSnapshot{Phase="failed",Status="Setup needs attention",Error="Fixture diagnostic"});
     if(screen=="restart")view.Render(new InstallerSnapshot{Phase="restart_required"});
     if(screen=="complete")view.Render(new InstallerSnapshot{Phase="complete",AppValidated=true,EnvironmentRequired=false});
     form.PerformLayout();Application.DoEvents();Readable(view,screen+(minimum?" minimum":" default"),factor);
     if(!minimum&&(factor==1.25f||factor==2f)&&(screen=="welcome"||screen=="options"||screen=="failed")){
      using(var bitmap=new Bitmap(view.Width,view.Height)){
       view.DrawToBitmap(bitmap,new Rectangle(Point.Empty,bitmap.Size));
       bitmap.Save(Path.Combine(args[1],"text-"+screen+"-"+(dark?"dark":"light")+"-"+(int)(factor*100)+".png"));
      }
     }
    }
   }
  }
 }
}
''', encoding='utf-8')
            binary = Path(folder) / 'TextScaleChecks.exe'
            compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
            files = [*sorted((ROOT / 'installer/native').glob('*.cs')),
                     *sorted((ROOT / 'installer/presentation').glob('*.cs')), source]
            build = subprocess.run([str(compiler), '/nologo', '/target:exe', '/main:TextScaleChecks',
                '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                '/reference:System.IO.Compression.dll', '/reference:Microsoft.CSharp.dll',
                '/reference:System.Web.Extensions.dll',
                '/resource:' + str(ROOT / 'tower-icons/engineer-monkey.png') + ',BloonsPlus.Engineer',
                '/out:' + str(binary), *map(str, files)],
                capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            artifacts = ROOT / '.superpowers/sdd/2026-10-06-installer-startup/text-scale-artifacts'
            artifacts.mkdir(parents=True, exist_ok=True)
            result = subprocess.run([str(binary), folder, str(artifacts)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
