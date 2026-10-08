import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InventoryTests(unittest.TestCase):
    def test_valid_runtime_map_changes_do_not_require_package_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'MutableMapChecks', r'''
using System;
using System.IO;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
internal static class MutableMapChecks {
 static void Check(bool value,string message){if(!value)throw new Exception(message);}
 static string Hash(string file){using(var hash=SHA256.Create())using(var input=File.OpenRead(file))return BitConverter.ToString(hash.ComputeHash(input)).Replace("-","").ToLowerInvariant();}
 static void Main(string[] args){
  string root=Path.Combine(args[0],"app");Directory.CreateDirectory(root);
  string app=Path.Combine(root,"Bloons+.exe"), maps=Path.Combine(root,"resources","app","autobtd6","maps.json"), immutable=Path.Combine(root,"maps.json");
  Directory.CreateDirectory(Path.GetDirectoryName(maps));
  File.WriteAllText(app,"fixture app");File.WriteAllText(immutable,"immutable");
  string original="{\"fixture_map\":{\"category\":\"beginner\",\"name\":\"Fixture Map\",\"page\":0,\"pos\":0}}";
  File.WriteAllText(maps,original);
  var serializer=new JavaScriptSerializer();string fingerprint=new string('a',64);
  File.WriteAllText(Path.Combine(root,"bloons-package.json"),serializer.Serialize(new {protocolVersion=1,version="0.1.39-preview.99",fingerprint=fingerprint,files=new[]{new {path="Bloons+.exe",sha256=Hash(app)},new {path="resources/app/autobtd6/maps.json",sha256=Hash(maps)},new {path="maps.json",sha256=Hash(immutable)}}}));
  Check(InstallerInventory.Inspect(root,fingerprint).FilesHealthy,"Baseline inventory is unhealthy");
  string learned="{\"fixture_map\":{\"category\":\"beginner\",\"name\":\"Fixture Map\",\"page\":1,\"pos\":5},\"new_fixture\":{\"category\":\"advanced\",\"name\":\"New Fixture\",\"page\":0,\"pos\":2}}";
  File.WriteAllText(maps,learned);
  Check(InstallerInventory.Inspect(root,fingerprint).FilesHealthy,"Valid learned map positions trigger a false repair");
  Check(InstallerInventory.Inspect(root,new string('b',64)).DifferentBuild,"Mutable maps hid a different package build");
  foreach(string bad in new[]{"{","[]","{}",learned.Replace("advanced","invalid"),learned.Replace("\"pos\":5","\"pos\":6"),learned.Replace("\"page\":1","\"page\":-1"),learned.Replace("\"page\":1","\"page\":1.5"),learned.Replace("\"pos\":5","\"pos\":true"),learned.Replace("new_fixture","../unsafe"),learned.Replace("new_fixture","new_fixture\\n"),learned.Replace("New Fixture",""),new string(' ',2*1024*1024)+learned}){
   File.WriteAllText(maps,bad);Check(!InstallerInventory.Inspect(root,fingerprint).FilesHealthy,"Malformed runtime map data accepted");
  }
  var tooMany=new System.Collections.Generic.Dictionary<string,object>();
  for(int i=0;i<2001;i++)tooMany["fixture_"+i]=new {category="beginner",name="Fixture",page=0,pos=0};
  File.WriteAllText(maps,serializer.Serialize(tooMany));Check(!InstallerInventory.Inspect(root,fingerprint).FilesHealthy,"Unbounded map count accepted");
  string nested=new string('[',80)+"0"+new string(']',80);
  File.WriteAllText(maps,learned.Replace("\"pos\":5","\"pos\":5,\"extra\":"+nested));
  Check(!InstallerInventory.Inspect(root,fingerprint).FilesHealthy,"Unbounded nested map data accepted");
  File.Delete(maps);Check(!InstallerInventory.Inspect(root,fingerprint).FilesHealthy,"Missing map table accepted");
  File.WriteAllText(maps,learned);File.WriteAllText(immutable,"changed");
  Check(!InstallerInventory.Inspect(root,fingerprint).FilesHealthy,"Other maps.json file escaped integrity checks");
  File.WriteAllText(immutable,"immutable");File.WriteAllText(app,"damaged");
  Check(!InstallerInventory.Inspect(root,fingerprint).FilesHealthy,"Damaged executable escaped integrity checks");
 }
}
''')
            result = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
  File.WriteAllText(Path.Combine(root,"bloons-package.json"),serializer.Serialize(new {protocolVersion=1,version="0.1.4-preview.99",fingerprint=new string('a',64),files=new[]{new {path="Bloons+.exe",sha256=Hash(app)},new {path="prefs.json",sha256=Hash(prefs)}}}));
  var observed=InstallerInventory.Inspect(root,new string('a',64));
  Check(observed.Exists&&observed.FilesHealthy&&!observed.DifferentBuild,"Observed installation missing");
  var welcome=InstallerViewState.Welcome(observed.Version,observed.FilesHealthy,observed.DifferentBuild);
  Check(welcome.Status.Contains("0.1.4-preview.99"),"Installed release version was not shown in the welcome view");
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
