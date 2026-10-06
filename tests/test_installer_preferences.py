import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class PreferencesTests(unittest.TestCase):
    def test_options_survive_reopen_without_loading_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'PreferenceChecks', r'''
using System;
using System.IO;
internal static class PreferenceChecks {
 static void Check(bool value,string message){if(!value)throw new Exception(message);}
 static void Main(string[] args){
  var options=new InstallerOptions(Path.Combine(args[0],"custom-app"),args[0],"unused.exe",false,null){LaunchAfterInstall=false,DesktopShortcut=true,StartMenuShortcut=false,RequestedVmSetup=false,RequestedIsoPath="custom.iso"};
  InstallerPreferences.Save(options);
  var reopened=InstallerPreferences.Load(new InstallerOptions(Path.Combine(args[0],"default-app"),args[0],"unused.exe",false,null));
  Check(reopened.InstallRoot==options.InstallRoot&&!reopened.LaunchAfterInstall&&reopened.DesktopShortcut&&!reopened.StartMenuShortcut&&!reopened.RequestedVmSetup&&reopened.RequestedIsoPath=="custom.iso","Saved choices were reset");
  File.WriteAllText(Path.Combine(args[0],"installer-preferences.json"),"bad");
  Check(InstallerPreferences.Load(options).InstallRoot==options.InstallRoot,"Malformed choices changed the fallback");
 }
}
''')
            result = subprocess.run([str(binary),folder],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
