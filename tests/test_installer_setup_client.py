import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerSetupClientTests(unittest.TestCase):
    def test_legacy_controller_404_uses_verified_private_port_and_reuses_it(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'LegacySetupChecks', r'''
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
internal static class LegacySetupChecks {
 static void Check(bool value,string why){if(!value)throw new Exception(why);}
 static void Main(){Run().GetAwaiter().GetResult();}
 static async Task Run(){
  string root=Path.Combine(Path.GetTempPath(),"Bloons-legacy-"+Guid.NewGuid().ToString("N"));
  string id=Guid.NewGuid().ToString("N"),owner=SetupControllerClient.Owner(Path.Combine(root,"resources","app"));
  var legacy=new TcpListener(IPAddress.Loopback,0);legacy.Start();int original=((IPEndPoint)legacy.LocalEndpoint).Port;
  TcpListener owned=null;Task ownedService=null;int launches=0,legacyGets=0,commands=0;bool secretSeen=false;
  var oldService=Task.Run(()=>{while(true){TcpClient socket;try{socket=legacy.AcceptTcpClient();}catch{break;}
   using(socket)using(var stream=socket.GetStream())using(var reader=new StreamReader(stream)){
    Check(reader.ReadLine()=="GET /api/setup/controller HTTP/1.1","Legacy controller received a mutation");
    string line;while(!String.IsNullOrEmpty(line=reader.ReadLine()))Check(!line.StartsWith("X-Bloons-Setup-Key",StringComparison.OrdinalIgnoreCase),"Legacy owner received secret");
    legacyGets++;byte[] bytes=System.Text.Encoding.ASCII.GetBytes("HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n");stream.Write(bytes,0,bytes.Length);
   }
  }});
  Action<int> launch=port=>{launches++;Check(port!=original,"Legacy port replaced");owned=new TcpListener(IPAddress.Loopback,port);owned.Start();
   ownedService=Task.Run(()=>{while(true){TcpClient socket;try{socket=owned.AcceptTcpClient();}catch{break;}
    using(socket)using(var stream=socket.GetStream())using(var reader=new StreamReader(stream,System.Text.Encoding.ASCII,false,1024,true)){
     string route=reader.ReadLine().Split(' ')[1],line;int length=0;
     while(!String.IsNullOrEmpty(line=reader.ReadLine())){if(line.StartsWith("Content-Length:",StringComparison.OrdinalIgnoreCase))length=Int32.Parse(line.Split(':')[1]);if(line.StartsWith("X-Bloons-Setup-Key",StringComparison.OrdinalIgnoreCase))secretSeen=true;}
     char[] body=new char[length];int count=0;while(count<length)count+=reader.Read(body,count,length-count);
     object result=route=="/api/setup/controller"?(object)new{protocolVersion=1,owner,pid=Process.GetCurrentProcess().Id,setupOnly=true}:(object)new{protocolVersion=1,sessionId=id,sequence=1,phase="validating"};
     if(route.EndsWith("command"))commands++;
     byte[] bytes=System.Text.Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(result));
     byte[] header=System.Text.Encoding.ASCII.GetBytes("HTTP/1.1 200 OK\r\nContent-Length: "+bytes.Length+"\r\nConnection: close\r\n\r\n");stream.Write(header,0,header.Length);stream.Write(bytes,0,bytes.Length);
    }
   }});
  };
  try{
   string executable=Process.GetCurrentProcess().MainModule.FileName;
   using(var client=new SetupControllerClient(root,root,id,original,executable,launch)){
    await client.ConnectAsync("install","",CancellationToken.None);await client.CommandAsync(1,"start",CancellationToken.None);
   }
   using(var client=new SetupControllerClient(root,root,id,original,executable,launch))await client.ConnectAsync("resume","",CancellationToken.None);
   Check(launches==1&&legacyGets==1&&commands==1&&secretSeen,"Private controller was duplicated or not authenticated");
  }finally{legacy.Stop();if(owned!=null)owned.Stop();if(Directory.Exists(root))Directory.Delete(root,true);}
  await oldService;if(ownedService!=null)await ownedService;
 }
}
''')
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_environment_handoff_keeps_selected_operation(self):
        source=(Path(__file__).resolve().parents[1]/'installer/native/WindowsInstallerOperations.cs').read_text()
        self.assertIn('ConnectAsync(options.Operation,',source)
        engine=(Path(__file__).resolve().parents[1]/'installer/native/InstallerEngine.cs').read_text()
        self.assertIn('options.Operation = session.Snapshot.Operation;',engine)

    def test_owned_protocol_handoff_and_async_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'SetupClientChecks', r'''
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Diagnostics;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
internal static class SetupClientChecks {
 static void Check(bool value,string why) { if (!value) throw new Exception(why); }
 static void Main(string[] args) { Run().GetAwaiter().GetResult(); }
 static async Task Run() {
  string root=Path.Combine(Path.GetTempPath(),"Bloons-client-"+Guid.NewGuid().ToString("N"));
  var listener=new TcpListener(IPAddress.Loopback,0);listener.Start();int port=((IPEndPoint)listener.LocalEndpoint).Port;
  string owner=SetupControllerClient.Owner(Path.Combine(root,"resources","app"));
  string executable=Process.GetCurrentProcess().MainModule.FileName;
  Check(SetupControllerClient.PortOwnedBy(port,Process.GetCurrentProcess().Id),"Listening port ownership was not observed");
  Check(!SetupControllerClient.PortOwnedBy(port,1),"Unrelated PID could impersonate port owner");
  int protocol=2; string reportedOwner=owner; int reportedPid=Process.GetCurrentProcess().Id;
  var serializer=new JavaScriptSerializer(); int commands=0; bool keySeen=false;string sessionId=Guid.NewGuid().ToString("N");
  bool rejectNextCommand=false;
  var service=Task.Run(()=> {
   while(true) {
    TcpClient socket;
    try { socket=listener.AcceptTcpClient(); } catch { break; }
    using(socket) using(var stream=socket.GetStream()) using(var reader=new StreamReader(stream,System.Text.Encoding.ASCII,false,1024,true)) {
    string route=reader.ReadLine().Split(' ')[1];
    var headers=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);string line;
    while(!String.IsNullOrEmpty(line=reader.ReadLine())) {int colon=line.IndexOf(':');headers[line.Substring(0,colon)]=line.Substring(colon+1).Trim();}
    object result;
    if(route=="/api/setup/controller") result=new {protocolVersion=protocol,owner=reportedOwner,pid=reportedPid};
    else {
     keySeen=headers.ContainsKey("X-Bloons-Setup-Key");
     int length=headers.ContainsKey("Content-Length")?Int32.Parse(headers["Content-Length"]):0;
     char[] body=new char[length];int read=0;while(read<length)read+=reader.Read(body,read,length-read);
     Check(!new string(body).Contains("key"),"Secret entered body");
     if(route.EndsWith("command")) {
      commands++;
      if(rejectNextCommand){rejectNextCommand=false;byte[] conflict=System.Text.Encoding.ASCII.GetBytes("HTTP/1.1 409 Conflict\r\nContent-Length: 0\r\nConnection: close\r\n\r\n");stream.Write(conflict,0,conflict.Length);continue;}
     }
     result=new {protocolVersion=1,sessionId,phase="validating",sequence=4};
    }
    byte[] bytes=System.Text.Encoding.UTF8.GetBytes(serializer.Serialize(result));
    byte[] header=System.Text.Encoding.ASCII.GetBytes("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "+bytes.Length+"\r\nConnection: close\r\n\r\n");
    stream.Write(header,0,header.Length);stream.Write(bytes,0,bytes.Length);
    }
   }
  });
  try {
   using(var client=new SetupControllerClient(root,root,sessionId,port,executable)) {
    try { await client.ConnectAsync("install","",CancellationToken.None);throw new Exception("Wrong protocol accepted"); } catch(InvalidDataException) {}
    protocol=1;reportedOwner=new string('f',64);
    try { await client.ConnectAsync("install","",CancellationToken.None);throw new Exception("Wrong owner accepted"); } catch(InvalidDataException) {}
    reportedOwner=owner;reportedPid=-1;
    try { await client.ConnectAsync("install","",CancellationToken.None);throw new Exception("Wrong process accepted"); } catch(InvalidDataException) {}
    reportedPid=Process.GetCurrentProcess().Id;
    var snapshot=await client.ConnectAsync("install","",CancellationToken.None);
    Check((string)snapshot["phase"]=="validating"&&keySeen,"Authenticated connect missing");
    await client.CommandAsync(4,"resume",CancellationToken.None);
    Check(commands==1,"Command missing");
    rejectNextCommand=true;
    await client.CommandFreshAsync("cancel",CancellationToken.None);
    Check(commands==3,"Stale cancellation was not re-observed and retried exactly once");
    await client.ObserveAsync(CancellationToken.None);
    Check(Directory.GetFiles(Path.Combine(root,"setup-handoff")).Length==1,"Private handoff missing");
   }
  } finally {listener.Stop(); if(Directory.Exists(root))Directory.Delete(root,true);}
  await service;
 }
}
''')
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
