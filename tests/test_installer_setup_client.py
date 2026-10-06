import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerSetupClientTests(unittest.TestCase):
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
     if(route.EndsWith("command")) commands++;
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
