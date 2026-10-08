# App Sandbox boot-file fallback. Only the newly attached guest disk is writable.
param([string]$WindowsRoot,[string]$EfiRoot,[string]$DiskFile,[int]$DiskNumber=-1,[switch]$LibraryOnly)
$ErrorActionPreference='Stop'

function Get-NormalizedGuestPath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { throw 'Missing guest path' }
    return [IO.Path]::GetFullPath($Path).TrimEnd('\')
}

function Get-GuestFileHash([string]$Path) {
    $stream=[IO.File]::OpenRead($Path); $hash=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-','') }
    finally { $hash.Dispose(); $stream.Dispose() }
}

function Assert-GuestBootLayout($Image,$Disk,$WindowsPartition,$EfiPartition,$WindowsVolume,$EfiVolume,
                              [string]$WindowsRoot,[string]$EfiRoot,[string]$DiskFile,[int]$DiskNumber) {
    $win=Get-NormalizedGuestPath $WindowsRoot; $efi=Get-NormalizedGuestPath $EfiRoot
    if (!$Image.Attached -or (Get-NormalizedGuestPath $Image.ImagePath) -ne (Get-NormalizedGuestPath $DiskFile) -or
        $DiskNumber -lt 0 -or $Disk.Number -ne $DiskNumber -or $Disk.IsBoot -or $Disk.IsSystem -or $Disk.PartitionStyle -ne 'GPT') {
        throw 'Boot repair requires the exact attached guest GPT disk'
    }
    if ($win -eq $efi -or $WindowsPartition.DiskNumber -ne $DiskNumber -or $EfiPartition.DiskNumber -ne $DiskNumber -or
        $WindowsPartition.PartitionNumber -ne 3 -or $EfiPartition.PartitionNumber -ne 1 -or
        $WindowsPartition.IsBoot -or $WindowsPartition.IsSystem -or
        [guid]$WindowsPartition.GptType -ne [guid]'ebd0a0a2-b9e5-4433-87c0-68b6b72699c7' -or
        [guid]$EfiPartition.GptType -ne [guid]'c12a7328-f81f-11d2-ba4b-00a0c93ec93b' -or
        $WindowsVolume.FileSystem -ne 'NTFS' -or $EfiVolume.FileSystem -ne 'FAT32' -or
        @($WindowsPartition.AccessPaths | Where-Object {(Get-NormalizedGuestPath $_) -eq $win}).Count -ne 1 -or
        @($EfiPartition.AccessPaths | Where-Object {(Get-NormalizedGuestPath $_) -eq $efi}).Count -ne 1) {
        throw 'Guest Windows/EFI partition identity or mount differs'
    }
    foreach ($id in @($Disk.Guid,$WindowsPartition.Guid,$EfiPartition.Guid)) {
        if ([guid]$id -eq [guid]::Empty) { throw 'Guest partition GUID is missing' }
    }
}

function Write-GuestSystemMarker([string]$Source,[string]$Output) {
    $sourcePath=Get-NormalizedGuestPath $Source; $outputPath=Get-NormalizedGuestPath $Output
    if (!(Test-Path -LiteralPath $sourcePath -PathType Leaf) -or (Get-Item -LiteralPath $sourcePath).Length -gt 2097152 -or
        (Test-Path -LiteralPath $outputPath) -or $sourcePath -eq $outputPath) { throw 'Fresh offline boot-store output required' }
    if (!('BloonsGuestOfflineHive' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class BloonsGuestOfflineHive {
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr LoadLibraryEx(string path, IntPtr file, uint flags);
 [DllImport("offreg.dll", CharSet=CharSet.Unicode)] static extern uint OROpenHive(string path,out IntPtr hive);
 [DllImport("offreg.dll")] static extern uint ORCloseHive(IntPtr hive);
 [DllImport("offreg.dll", CharSet=CharSet.Unicode)] static extern uint OROpenKey(IntPtr root,string path,out IntPtr key);
 [DllImport("offreg.dll")] static extern uint ORCloseKey(IntPtr key);
 [DllImport("offreg.dll", CharSet=CharSet.Unicode)] static extern uint OREnumKey(IntPtr key,uint index,StringBuilder name,ref uint length,IntPtr cls,IntPtr clsLength,IntPtr time);
 [DllImport("offreg.dll", CharSet=CharSet.Unicode)] static extern uint OREnumValue(IntPtr key,uint index,StringBuilder name,ref uint length,out uint type,byte[] data,ref uint size);
 [DllImport("offreg.dll", CharSet=CharSet.Unicode)] static extern uint ORSetValue(IntPtr key,string name,uint type,byte[] data,uint size);
 [DllImport("offreg.dll", CharSet=CharSet.Unicode)] static extern uint ORSaveHive(IntPtr hive,string path,uint major,uint minor);
 static void Check(uint code) { if(code!=0) throw new IOException("Offline boot-store Windows error " + code); }
 sealed class State {
  public HashSet<string> Keys=new HashSet<string>(StringComparer.Ordinal);
  public Dictionary<string,string> Values=new Dictionary<string,string>(StringComparer.Ordinal);
  public int Bytes;
 }
 static State Snapshot(IntPtr hive) { var state=new State(); Visit(hive,"",0,state); return state; }
 static void Visit(IntPtr key,string path,int depth,State state) {
  if(depth>16 || state.Keys.Count>=2000) throw new IOException("Boot-store key budget exceeded");
  state.Keys.Add(path);
  for(uint i=0;;i++) {
   if(i>=2000) throw new IOException("Boot-store value budget exceeded");
   var name=new StringBuilder(512); uint length=512,type,size=65536; var data=new byte[65536];
   uint code=OREnumValue(key,i,name,ref length,out type,data,ref size); if(code==259) break; Check(code);
   if(length>=512 || size>65536 || state.Values.Count>=2000 || (state.Bytes+=(int)size)>2097152) throw new IOException("Boot-store value bounds exceeded");
   state.Values.Add(path+"\0"+name.ToString(),type+":"+Convert.ToBase64String(data,0,(int)size));
  }
  for(uint i=0;;i++) {
   if(i>=2000) throw new IOException("Boot-store child budget exceeded");
   var name=new StringBuilder(512); uint length=512;
   uint code=OREnumKey(key,i,name,ref length,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero); if(code==259) break; Check(code);
   if(length>=512) throw new IOException("Boot-store name bounds exceeded");
   IntPtr child; Check(OROpenKey(key,name.ToString(),out child));
   try { Visit(child,path+"/"+name,depth+1,state); } finally { Check(ORCloseKey(child)); }
  }
 }
 static void Equal(State expected,State actual) {
  if(!expected.Keys.SetEquals(actual.Keys) || expected.Values.Count!=actual.Values.Count) throw new IOException("Boot-store contents differ");
  foreach(var item in expected.Values) { string value; if(!actual.Values.TryGetValue(item.Key,out value) || item.Value!=value) throw new IOException("Boot-store value differs"); }
 }
 public static void Write(string source,string output) {
  if(File.Exists(output)) throw new IOException("Boot-store output already exists");
  // Absolute Windows library, no downloads, registry mounts or default BCD store.
  if(LoadLibraryEx(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),"offreg.dll"),IntPtr.Zero,0x800)==IntPtr.Zero) throw new IOException("Windows offline hive API unavailable");
  IntPtr root=IntPtr.Zero,description=IntPtr.Zero,readback=IntPtr.Zero;
  try {
   Check(OROpenHive(source,out root)); var before=Snapshot(root); string marker="/Description\0System",value;
   if(before.Values.TryGetValue(marker,out value) && !value.StartsWith("4:",StringComparison.Ordinal)) throw new IOException("Unexpected boot-store System value type");
   Check(OROpenKey(root,"Description",out description)); Check(ORSetValue(description,"System",4,new byte[]{1,0,0,0},4));
   Check(ORCloseKey(description)); description=IntPtr.Zero;
   before.Values[marker]="4:AQAAAA=="; Equal(before,Snapshot(root));
   Check(ORSaveHive(root,output,6,1)); Check(ORCloseHive(root)); root=IntPtr.Zero;
   Check(OROpenHive(output,out readback)); Equal(before,Snapshot(readback));
  } finally {
   try { if(description!=IntPtr.Zero) Check(ORCloseKey(description)); }
   finally { try { if(readback!=IntPtr.Zero) Check(ORCloseHive(readback)); } finally { if(root!=IntPtr.Zero) Check(ORCloseHive(root)); } }
  }
 }
}
'@
    }
    $before=Get-GuestFileHash $sourcePath
    [BloonsGuestOfflineHive]::Write($sourcePath,$outputPath)
    if ((Get-GuestFileHash $sourcePath) -ne $before) { throw 'Source boot store changed' }
}

function Repair-GuestBootStore([string]$WindowsRoot,[string]$EfiRoot,[string]$DiskFile,[int]$DiskNumber) {
    $win=Get-NormalizedGuestPath $WindowsRoot; $efi=Get-NormalizedGuestPath $EfiRoot
    $image=Get-DiskImage -ImagePath $DiskFile; $disk=$image | Get-Disk
    $wp=Get-Partition -DiskNumber $DiskNumber -PartitionNumber 3; $ep=Get-Partition -DiskNumber $DiskNumber -PartitionNumber 1
    Assert-GuestBootLayout $image $disk $wp $ep ($wp | Get-Volume) ($ep | Get-Volume) $win $efi $DiskFile $DiskNumber
    $template=Join-Path $win 'Windows\System32\config\BCD-Template'
    if (!(Test-Path -LiteralPath (Join-Path $win 'Windows\System32\ntoskrnl.exe'))) { throw 'Guest Windows image missing' }
    $templateHash=Get-GuestFileHash $template
    $boot=Join-Path $efi 'EFI\Microsoft\Boot'; $store=Join-Path $boot 'BCD'
    New-Item -ItemType Directory -Path $boot -Force | Out-Null
    $work=Join-Path $boot ('bloons-repair-'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $work | Out-Null
    $copy=Join-Path $work 'BCD'; $qualified=Join-Path $work 'BCD-qualified'; $marked=Join-Path $work 'BCD-system'
    $tool=Join-Path $env:SystemRoot 'System32\bcdedit.exe'
    function Invoke-GuestStore([string[]]$Arguments,[string]$Path=$copy) {
        # Windows PowerShell wraps native stderr as ErrorRecord objects. Collect
        # the complete diagnostic before deciding from the native exit code.
        $previousPreference=$ErrorActionPreference
        try {
            $ErrorActionPreference='Continue'
            $output=@(& $tool /store $Path @Arguments 2>&1)
            $code=$LASTEXITCODE
        } finally { $ErrorActionPreference=$previousPreference }
        if ($code -ne 0) { throw ('Explicit guest boot-store operation failed ('+$code+', '+($Arguments -join ' ')+'): '+($output -join ' ')) }
        return ($output -join "`n")
    }
    try {
        [IO.File]::Copy($template,$copy,$false)
        # Microsoft's template has no display order; /copy requires one.
        Invoke-GuestStore @('/displayorder','{a1943bbc-ea85-487c-97c7-c9ede908a38a}') | Out-Null
        $loaderText=Invoke-GuestStore @('/copy','{a1943bbc-ea85-487c-97c7-c9ede908a38a}','/d','Windows')
        $loader=[regex]::Match($loaderText,'\{[0-9a-fA-F-]{36}\}').Value
        if (!$loader) { throw 'Guest loader identifier missing' }
        foreach ($stepArgs in @(
            @('/set',$loader,'path','\Windows\System32\winload.efi'),
            @('/set',$loader,'systemroot','\Windows'),
            @('/set','{bootmgr}','path','\EFI\Microsoft\Boot\bootmgfw.efi'),
            @('/default',$loader),@('/displayorder',$loader),@('/timeout','0')
        )) { Invoke-GuestStore $stepArgs | Out-Null }
        $providerPath='\??\'+$copy
        $class=Get-CimClass -Namespace root/WMI -ClassName BcdStore
        $opened=Invoke-CimMethod -CimClass $class -MethodName OpenStore -Arguments @{File=$copy}
        if (!$opened.ReturnValue -or !$opened.Store -or $opened.Store.FilePath -ne $providerPath) { throw 'Explicit guest store open failed' }
        $diskGuid='{'+([guid]$disk.Guid).ToString()+'}'
        foreach ($spec in @(
            @{id=$loader;type=[uint32]0x11000001;part=$wp.Guid},
            @{id=$loader;type=[uint32]0x21000001;part=$wp.Guid},
            @{id='{9dea862c-5cdd-4e70-acc1-f32b344d4795}';type=[uint32]0x11000001;part=$ep.Guid}
        )) {
            $object=Invoke-CimMethod -InputObject $opened.Store -MethodName OpenObject -Arguments @{Id=$spec.id}
            if (!$object.ReturnValue -or !$object.Object -or $object.Object.StoreFilePath -ne $providerPath -or $object.Object.Id -ne $spec.id) { throw 'Guest boot object identity differs' }
            $part='{'+([guid]$spec.part).ToString()+'}'
            $set=Invoke-CimMethod -InputObject $object.Object -MethodName SetQualifiedPartitionDeviceElement -Arguments @{Type=$spec.type;PartitionStyle=[uint32]1;DiskSignature=$diskGuid;PartitionIdentifier=$part}
            if (!$set.ReturnValue) { throw 'Guest boot device write failed' }
            $read=Invoke-CimMethod -InputObject $object.Object -MethodName GetElementWithFlags -Arguments @{Type=$spec.type;Flags=[uint32]1}
            $device=$read.Element.Device
            if (!$read.ReturnValue -or $device.DeviceType -ne 6 -or $device.PartitionStyle -ne 1 -or [guid]$device.DiskSignature -ne [guid]$diskGuid -or [guid]$device.PartitionIdentifier -ne [guid]$part) { throw 'Guest boot device readback differs' }
        }
        $before=Invoke-GuestStore @('/enum','all','/v')
        if ($before -match '(?im)^\s*(device|osdevice)\s+vhd=') { throw 'Host VHD reference remains in guest store' }
        [IO.File]::Copy($copy,$qualified,$false)
        Write-GuestSystemMarker $qualified $marked
        $after=Invoke-GuestStore @('/enum','all','/v') $marked
        if ($before -ne $after -or (Get-GuestFileHash $template) -ne $templateHash) { throw 'Guest boot-store verification differs' }
        # Re-observe identities at the write boundary; never touch a host boot store.
        $image=Get-DiskImage -ImagePath $DiskFile; $disk=$image | Get-Disk
        $wp=Get-Partition -DiskNumber $DiskNumber -PartitionNumber 3; $ep=Get-Partition -DiskNumber $DiskNumber -PartitionNumber 1
        Assert-GuestBootLayout $image $disk $wp $ep ($wp | Get-Volume) ($ep | Get-Volume) $win $efi $DiskFile $DiskNumber
        foreach ($entry in Get-ChildItem -LiteralPath (Join-Path $win 'Windows\Boot\EFI')) {
            Copy-Item -LiteralPath $entry.FullName -Destination $boot -Recurse -Force
        }
        foreach ($folder in @('Fonts','Resources')) {
            $source=Join-Path $win ('Windows\Boot\'+$folder)
            if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $boot $folder) -Recurse -Force }
        }
        $fallback=Join-Path $efi 'EFI\Boot'; New-Item -ItemType Directory -Path $fallback -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $boot 'bootmgfw.efi') -Destination (Join-Path $fallback 'bootx64.efi') -Force
        if (Test-Path -LiteralPath $store) { [IO.File]::Copy($store,(Join-Path $work 'BCD-before'),$false) }
        $expected=Get-GuestFileHash $marked
        [IO.File]::Copy($marked,$store,$true)
        if ((Get-GuestFileHash $store) -ne $expected) { throw 'Installed guest boot store differs' }
        Write-Output 'Guest UEFI boot files repaired and verified'
    } finally {
        # Keep the small guest-local repair evidence; the helper owns disk/mount cleanup.
    }
}

if (!$LibraryOnly) {
    try { Repair-GuestBootStore $WindowsRoot $EfiRoot $DiskFile $DiskNumber }
    catch { Write-Error $_; exit 1 }
}
