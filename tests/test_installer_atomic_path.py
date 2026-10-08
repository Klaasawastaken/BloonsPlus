"""Native handoff writes must not exceed MAX_PATH solely because of temp suffixes."""
import os
import subprocess
import tempfile
import unittest

from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native file operations')
class InstallerAtomicPathTests(unittest.TestCase):
    def test_valid_long_handoff_path_creates_replaces_and_preserves_on_failure(self):
        with tempfile.TemporaryDirectory(prefix='bloons-atomic-path-') as folder:
            binary = compile_harness(folder, 'AtomicPathChecks', r'''
using System;
using System.IO;
internal static class AtomicPathChecks {
 static void Check(bool ok,string message){if(!ok)throw new Exception(message);}
 static void Main(string[] args) {
  string parent=Path.GetFullPath(args[0]);
  string root=Path.Combine(parent,new string('x',158-parent.Length-1));
  Check(root.Length==158,"Wrong native boundary fixture");
  Directory.CreateDirectory(root);
  string destination=Path.Combine(root,new string('a',64)+".controller.json");
  Check(destination.Length==239,"Valid final handoff path changed");
  Check((destination+"."+Guid.NewGuid().ToString("N")+".tmp").Length>=260,"Old temporary path must reproduce overflow");
  string sentinel=Path.Combine(root,"unrelated.tmp");
  File.WriteAllText(sentinel,"preserve unrelated file");
  InstallSession.AtomicWrite(destination,"first checkpoint — preserved Unicode");
  Check(File.ReadAllText(destination)=="first checkpoint — preserved Unicode","Initial handoff differs");
  InstallSession.AtomicWrite(destination,"second checkpoint");
  Check(File.ReadAllText(destination)=="second checkpoint","Atomic replacement differs");
  using(var locked=File.Open(destination,FileMode.Open,FileAccess.Read,FileShare.None)) {
   bool rejected=false;
   try{InstallSession.AtomicWrite(destination,"must not replace");}catch(IOException){rejected=true;}
   Check(rejected,"Locked checkpoint replacement was accepted");
  }
  Check(File.ReadAllText(destination)=="second checkpoint","Failed write lost the original checkpoint");
  Check(File.ReadAllText(sentinel)=="preserve unrelated file","Cleanup deleted unrelated data");
  Check(Directory.GetFiles(root).Length==2,"Temporary checkpoint leaked after success/failure");
  string deep=Path.Combine(parent,new string('y',226-parent.Length-1));
  Directory.CreateDirectory(deep);
  string checkpoint=Path.Combine(deep,"session.json");
  Check(checkpoint.Length==239,"Short-basename boundary changed");
  InstallSession.AtomicWrite(checkpoint,"deep checkpoint");
  InstallSession.AtomicWrite(checkpoint,"deep replacement");
  Check(File.ReadAllText(checkpoint)=="deep replacement","Deep checkpoint was not replaced");
  Check(Directory.GetFiles(deep).Length==1,"Deep checkpoint leaked a temporary file");
  string occupied=Path.Combine(deep,new string('c',32));
  File.WriteAllText(occupied,"unrelated occupied name");
  int names=0;
  InstallSession.AtomicWrite(checkpoint,"collision retry",()=>++names==1?new string('c',32):new string('d',32));
  Check(names==2,"Temporary-name collision did not retry once");
  Check(File.ReadAllText(occupied)=="unrelated occupied name","Collision cleanup deleted another writer's file");
  names=0; bool exhausted=false;
  try{InstallSession.AtomicWrite(checkpoint,"must not replace",()=>{names++;return new string('c',32);});}catch(IOException){exhausted=true;}
  Check(exhausted && names==16,"Temporary-name retries were not bounded");
  Check(File.ReadAllText(checkpoint)=="collision retry","Collision exhaustion lost checkpoint");
  Check(File.ReadAllText(occupied)=="unrelated occupied name","Collision exhaustion deleted unrelated data");
  Check(Directory.GetFiles(deep).Length==2,"Collision path leaked a temporary file");
  string narrow=Path.Combine(parent,new string('z',236-parent.Length-1));
  Directory.CreateDirectory(narrow);
  string narrowCheckpoint=Path.Combine(narrow,"session.json");
  InstallSession.AtomicWrite(narrowCheckpoint,"reduced filename budget");
  Check(File.ReadAllText(narrowCheckpoint)=="reduced filename budget","Reduced filename budget was not honored");
  Check(Directory.GetFiles(narrow).Length==1,"Reduced budget leaked a temporary file");
  Console.WriteLine("Native 239-character handoff create/replace/locked preservation passed");
 }
}
''')
            result = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
