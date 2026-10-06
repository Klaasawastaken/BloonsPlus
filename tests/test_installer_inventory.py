import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InventoryTests(unittest.TestCase):
    def test_observed_health_and_selective_uninstall_preserve_modified_data(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'InventoryChecks', r'''
using System;
using System.IO;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
internal static class InventoryChecks {
 static void Check(bool value,string message){if(!value)throw new Exception(message);}
 static string Hash(string file){using(var hash=SHA256.Create())using(var input=File.OpenRead(file))return BitConverter.ToString(hash.ComputeHash(input)).Replace("-","").ToLowerInvariant();}
 static void Main(string[] args){
  string root=Path.Combine(args[0],"app");Directory.CreateDirectory(root);
  string app=Path.Combine(root,"Bloons+.exe"),prefs=Path.Combine(root,"prefs.json");File.WriteAllText(app,"fixture");File.WriteAllText(prefs,"original");
  var serializer=new JavaScriptSerializer();
  File.WriteAllText(Path.Combine(root,"bloons-package.json"),serializer.Serialize(new {protocolVersion=1,version="0.1.0",fingerprint=new string('a',64),files=new[]{new {path="Bloons+.exe",sha256=Hash(app)},new {path="prefs.json",sha256=Hash(prefs)}}}));
  var observed=InstallerInventory.Inspect(root,new string('a',64));
  Check(observed.Exists&&observed.FilesHealthy&&!observed.DifferentBuild,"Observed installation missing");
  Check(InstallerInventory.Inspect(root,new string('b',64)).DifferentBuild,"Different package not detected");
  File.WriteAllText(prefs,"user change");File.WriteAllText(Path.Combine(root,"save.json"),"never delete");
  Check(!InstallerInventory.Inspect(root,new string('a',64)).FilesHealthy,"Modified required file accepted");
  int removed=InstallerInventory.RemoveUnchangedFiles(root);
  Check(removed==1&&!File.Exists(app)&&File.ReadAllText(prefs)=="user change"&&File.Exists(Path.Combine(root,"save.json")),"Uninstall removed private or modified data");
  string configuration=Path.Combine(root,"resources","app","data","config","calibration.json");Directory.CreateDirectory(Path.GetDirectoryName(configuration));File.WriteAllText(configuration,"unchanged user calibration");
  File.WriteAllText(Path.Combine(root,"bloons-package.json"),serializer.Serialize(new {protocolVersion=1,version="0.1.0",files=new[]{new {path="resources/app/data/config/calibration.json",sha256=Hash(configuration)}}}));
  Check(InstallerInventory.RemoveUnchangedFiles(root)==0&&File.Exists(configuration),"Unchanged user configuration was deleted");
  File.WriteAllText(Path.Combine(root,"bloons-package.json"),serializer.Serialize(new {protocolVersion=1,version="0.1.0",files=new[]{new {path="../outside",sha256=new string('c',64)}}}));
  bool blocked=false;try{InstallerInventory.RemoveUnchangedFiles(root);}catch(InvalidDataException){blocked=true;}
  Check(blocked,"Unsafe manifest path was accepted");
 }
}
''')
            result = subprocess.run([str(binary),folder],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
