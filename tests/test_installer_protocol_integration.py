"""Real native/Node setup transport; environment operators remain isolated fakes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

from native_installer_harness import ROOT, compile_harness


CONTROLLER = r'''
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { createSetupController } = require(process.argv[2]);
const root = process.argv[3];
const stages = ['vmp', 'appsandbox', 'daemon', 'iso', 'vm', 'provision', 'connected', 'steam'];
let replay = { running: true }, starts = 0, cancels = 0, releases = 0;
let status = pending();
function pending() {
  return { applicable: true, allDone: false, next: { id: 'provision' },
    steps: stages.map(id => ({ id, done: false })), job: { running: false } };
}
const dependencies = {
  getStatus: async fresh => { if (fresh !== true) throw Error('Readiness was not fresh'); return status; },
  getReplayStatus: async () => replay,
  start: async options => {
    if (options.operation !== 'install') throw Error('Installation intent changed');
    starts++; status.job = { running: true, stepId: 'provision' };
  },
  cancel: async () => { cancels++; },
  release: () => { releases++; },
};
const controller = createSetupController({ root: path.join(root, 'resources', 'app'),
  dataRoot: root, port: 0, dependencies, setupOnly: true });
const server = http.createServer(async (req, res) => {
  const route = new URL(req.url, 'http://127.0.0.1').pathname;
  // This private fixture changes observations only. It imports no VM/game operator.
  if (req.method === 'GET' && route.startsWith('/fixture/')) {
    switch (route.slice('/fixture/'.length)) {
      case 'idle': replay = { running: false }; break;
      case 'bytes': status.job = { running: true, stepId: 'iso', numerator: 42,
        denominator: 100, scope: 'Download' }; break;
      case 'stopped': status.job = { running: false }; break;
      case 'restart': status.job = { running: false, state: 'restart-required' }; break;
      case 'ready': status = { applicable: true, allDone: true,
        steps: stages.map(id => ({ id, done: true })), job: { running: false } }; break;
      case 'stats': break;
      default: res.writeHead(404); res.end(); return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ starts, cancels, releases })); return;
  }
  if (!route.startsWith('/api/setup/')) { res.writeHead(503); res.end(); return; }
  await controller.handle(req, res, route);
});
server.listen(0, '127.0.0.1', () => {
  const port = server.address().port; controller.setPort(port);
  fs.writeFileSync(path.join(root, 'ready.json'), JSON.stringify({ port, pid: process.pid }));
});
'''


NATIVE = r'''
using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
internal static class SetupIntegrationChecks {
 static void Check(bool value, string message) { if (!value) throw new Exception(message); }
 static string Text(Dictionary<string,object> snapshot, string key) {
  object value; return snapshot.TryGetValue(key, out value) ? value as string : null;
 }
 static Dictionary<string,object> Control(int port, string action) {
  var request=(HttpWebRequest)WebRequest.Create("http://127.0.0.1:"+port+"/fixture/"+action);
  request.Proxy=null; request.Timeout=5000;
  using(var response=request.GetResponse())using(var reader=new StreamReader(response.GetResponseStream()))
   return new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(reader.ReadToEnd());
 }
 static void Main(string[] args) {
  try { Run(args).GetAwaiter().GetResult(); }
  catch(Exception error) { Console.Error.WriteLine(error.Message); Environment.Exit(1); }
 }
 static async Task Run(string[] args) {
  string root=args[0], executable=args[1], id=Guid.NewGuid().ToString("N"); int port=Int32.Parse(args[2]);
  var token=CancellationToken.None;
  using(var client=new SetupControllerClient(root,root,id,port,executable)) {
   var snapshot=await client.ConnectAsync("install","",token);
   Check(Text(snapshot,"phase")=="idle","Native handoff did not reach the actual coordinator");
   snapshot=await client.CommandFreshAsync("start",token);
   Check(Text(snapshot,"humanAction")=="wait_replay" && (bool)snapshot["queued"],"Healthy replay was not protected");
   Check((int)Control(port,"stats")["starts"]==0,"Operator ran during gameplay");
   try { await client.ReleaseAsync(token); throw new Exception("Premature release accepted"); }
   catch(WebException error) {
    using(var response=error.Response as HttpWebResponse)
     Check(response!=null && response.StatusCode==HttpStatusCode.Conflict,"Premature release failed for the wrong reason");
   }
   Control(port,"idle"); snapshot=await client.ObserveAsync(token);
   Check(Text(snapshot,"phase")=="configuring_guest" && (int)Control(port,"stats")["starts"]==1,"Queued setup did not start exactly once at idle");
   Control(port,"bytes"); snapshot=await client.ObserveAsync(token);
   Check(Text(snapshot,"phase")=="downloading" && !(bool)snapshot["indeterminate"] &&
    Convert.ToInt64(snapshot["numerator"])==42 && Convert.ToInt64(snapshot["denominator"])==100 &&
    Text(snapshot,"scope")=="Download","Measured progress did not cross the real protocol");
   snapshot=await client.CommandFreshAsync("cancel",token);
   Check(Text(snapshot,"phase")=="recovering" && (int)Control(port,"stats")["cancels"]==1,"Cancellation did not retain the active owner");
   snapshot=await client.ObserveAsync(token);
   Check(Text(snapshot,"phase")=="recovering" && !SetupEnvironmentResult.FromSnapshot(snapshot).Ready,"Running cancelled work appeared complete");
   Control(port,"stopped"); snapshot=await client.ObserveAsync(token);
   Check(Text(snapshot,"phase")=="cancelled" && Text(snapshot,"humanAction")=="resume","Safe cancellation lost Resume");
   snapshot=await client.CommandFreshAsync("resume",token);
   Check(Text(snapshot,"phase")=="configuring_guest" && (int)Control(port,"stats")["starts"]==2,"Resume duplicated or lost the operator");
   // A new native client must reconnect to the same coordinator without restarting work.
   using(var reconnected=new SetupControllerClient(root,root,id,port,executable)) {
    snapshot=await reconnected.ConnectAsync("resume","",token);
    Check(Text(snapshot,"sessionId")==id && Text(snapshot,"operation")=="install" &&
     (int)Control(port,"stats")["starts"]==2,"Reconnect lost installation intent or duplicated work");
    snapshot=await reconnected.ObserveAsync(token);
    Check((bool)snapshot["indeterminate"] && snapshot["numerator"]==null,"Unknown next-stage progress retained old bytes");
    Control(port,"restart"); snapshot=await reconnected.ObserveAsync(token);
    var result=SetupEnvironmentResult.FromSnapshot(snapshot);
    Check(result.RestartRequired && !result.Ready,"Native model misread restart-required state");
    snapshot=await reconnected.CommandFreshAsync("restart_later",token);
    Check((bool)snapshot["restartDeferred"],"Restart Later was not persisted");
    string checkpoint=Directory.GetFiles(Path.Combine(root,"setup-sessions"),"session.json",SearchOption.AllDirectories)[0];
    string saved=File.ReadAllText(checkpoint);
    Check(saved.Contains("\"restartDeferred\":true") && !saved.Contains("\"key\""),"Checkpoint lost Later or exposed the transport secret");
    Control(port,"ready"); snapshot=await reconnected.ObserveAsync(token);
    result=SetupEnvironmentResult.FromSnapshot(snapshot);
    Check(result.Ready && !result.RestartRequired && Convert.ToInt32(snapshot["completedWeight"])==100,
     "Fresh ready environment did not reach validated native completion");
    await reconnected.ReleaseAsync(token);
    // Release is asynchronous in the actual Node handler; observe its receipt boundedly.
    int releases=0;
    for(int attempt=0;attempt<20 && releases==0;attempt++) {
     releases=(int)Control(port,"stats")["releases"]; if(releases==0)await Task.Delay(25);
    }
    Check(releases==1,"Validated setup-only controller was not released exactly once");
   }
  }
  Console.WriteLine("Native/Node protocol: replay boundary, bytes, cancellation, resume, reconnect, restart and validated release pass.");
 }
}
'''


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler and process ownership API')
class InstallerProtocolIntegrationTests(unittest.TestCase):
    def test_real_native_client_and_node_coordinator_recovery_contract(self):
        run = self.exercise_protocol()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn('validated release pass', run.stdout)

    def test_acceptance_rejects_a_coordinator_that_ignores_the_replay_boundary(self):
        run = self.exercise_protocol(bypass_replay_guard=True)
        self.assertNotEqual(run.returncode, 0, 'Acceptance failed to detect a broken replay guard')
        self.assertIn('Healthy replay was not protected', run.stderr)

    def exercise_protocol(self, bypass_replay_guard=False):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is required for native/coordinator acceptance')
        with tempfile.TemporaryDirectory(prefix='bloons-setup-protocol-') as folder:
            root = Path(folder)
            fixture = root / 'controller.cjs'
            fixture.write_text(CONTROLLER, encoding='utf-8')
            module = ROOT / 'lib/setup-controller.js'
            if bypass_replay_guard:
                # Mutate an isolated source copy to prove this acceptance check
                # detects unsafe setup. Production sources remain untouched.
                modules = root / 'modules'
                modules.mkdir()
                module = modules / 'setup-controller.js'
                shutil.copyfile(ROOT / 'lib/setup-controller.js', module)
                session = (ROOT / 'lib/setup-session.js').read_text(encoding='utf-8')
                guard = 'if (!replay || replay.running !== false)'
                self.assertEqual(session.count(guard), 1, 'Replay guard changed; review the negative fixture')
                (modules / 'setup-session.js').write_text(session.replace(guard, 'if (false)'), encoding='utf-8')
                (root / 'package.json').write_text('{"version":"acceptance-fixture"}', encoding='utf-8')
            binary = compile_harness(root, 'SetupIntegrationChecks', NATIVE)
            child = subprocess.Popen([node, str(fixture), str(module), str(root)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                deadline = time.monotonic() + 10
                while not (root / 'ready.json').exists() and child.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                if not (root / 'ready.json').exists():
                    self.fail('Isolated controller did not become ready')
                readiness = json.loads((root / 'ready.json').read_text())
                self.assertEqual(readiness['pid'], child.pid)
                run = subprocess.run([str(binary), str(root), str(Path(node).resolve()), str(readiness['port'])],
                    capture_output=True, text=True, timeout=45, creationflags=subprocess.CREATE_NO_WINDOW)
                self.assertIsNone(child.poll(), 'Coordinator exited before fixture cleanup')
            finally:
                if child.poll() is None:
                    child.terminate()
                stdout, stderr = child.communicate(timeout=10)
            self.assertEqual(stderr, b'', stderr.decode(errors='replace'))
            return run


if __name__ == '__main__':
    unittest.main()
