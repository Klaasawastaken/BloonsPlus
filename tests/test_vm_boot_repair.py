"""Synthetic guest-layout and offline-hive checks; no VM or host store mutation."""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'vm' / 'boot-store-repair.ps1'
SCRATCH = ROOT / '.superpowers'


@unittest.skipUnless(os.name == 'nt', 'Windows native APIs required')
class GuestBootRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SCRATCH.mkdir(exist_ok=True)

    def test_template_display_order_is_initialized_before_loader_copy(self):
        # The real Windows template has no display order. BCDEdit /copy fails
        # with "Element not found" unless it is initialized first.
        text=SCRIPT.read_text(encoding='utf-8')
        initialize="Invoke-GuestStore @('/displayorder','{a1943bbc-ea85-487c-97c7-c9ede908a38a}')"
        copy="$loaderText=Invoke-GuestStore @('/copy'"
        self.assertIn(initialize,text)
        self.assertLess(text.index(initialize),text.index(copy))

    def invoke(self, body, *arguments):
        self.assertTrue(SCRIPT.is_file(), 'production boot repair is missing')
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            harness = Path(temporary) / 'check.ps1'
            harness.write_text("param([string]$Module,[string]$Source,[string]$Output)\n$ErrorActionPreference='Stop'\n. $Module -LibraryOnly\n" + body, encoding='utf-8')
            result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(harness), str(SCRIPT), *arguments], capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            return json.loads(result.stdout)

    def test_partition_guards_reject_host_and_wrong_mounts(self):
        result = self.invoke(r"""
$image=[pscustomobject]@{Attached=$true;ImagePath='C:\Fixture\new.vhdx'}
$disk=[pscustomobject]@{Number=7;IsBoot=$false;IsSystem=$false;PartitionStyle='GPT';Guid='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}
$win=[pscustomobject]@{DiskNumber=7;PartitionNumber=3;IsBoot=$false;IsSystem=$false;GptType='ebd0a0a2-b9e5-4433-87c0-68b6b72699c7';Guid='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';AccessPaths=@('C:\Fixture\Windows\')}
$efi=[pscustomobject]@{DiskNumber=7;PartitionNumber=1;GptType='c12a7328-f81f-11d2-ba4b-00a0c93ec93b';Guid='cccccccc-cccc-cccc-cccc-cccccccccccc';AccessPaths=@('C:\Fixture\EFI\')}
$wv=[pscustomobject]@{FileSystem='NTFS'};$ev=[pscustomobject]@{FileSystem='FAT32'}
function Check { Assert-GuestBootLayout $image $disk $win $efi $wv $ev 'C:\Fixture\Windows' 'C:\Fixture\EFI' 'C:\Fixture\new.vhdx' 7 }
Check
$rejected=0
foreach($case in 1..9){
 switch($case){
  1{$disk.IsBoot=$true};2{$disk.IsSystem=$true};3{$image.Attached=$false}
  4{$disk.Number=8};5{$win.DiskNumber=8};6{$win.AccessPaths=@('C:\Wrong\')}
  7{$efi.GptType=$win.GptType};8{$wv.FileSystem='FAT32'};9{$image.ImagePath='C:\Wrong.vhdx'}
 }
 try{Check}catch{$rejected++}
 $disk.IsBoot=$false;$disk.IsSystem=$false;$image.Attached=$true;$disk.Number=7;$win.DiskNumber=7
 $win.AccessPaths=@('C:\Fixture\Windows\');$efi.GptType='c12a7328-f81f-11d2-ba4b-00a0c93ec93b';$wv.FileSystem='NTFS';$image.ImagePath='C:\Fixture\new.vhdx'
}
@{rejected=$rejected;positive=$true}|ConvertTo-Json -Compress
""")
        self.assertEqual(result, {'rejected': 9, 'positive': True})

    @staticmethod
    def native():
        lib = C.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'offreg.dll'))
        handle, uint, wide = C.c_void_p, C.c_uint32, C.c_wchar_p
        pointer = C.POINTER
        for name, args in {
            'ORCreateHive': [pointer(handle)], 'ORCloseHive': [handle],
            'ORCreateKey': [handle, wide, wide, uint, handle, pointer(handle), pointer(uint)],
            'OROpenHive': [wide, pointer(handle)], 'OROpenKey': [handle, wide, pointer(handle)],
            'ORCloseKey': [handle], 'ORSetValue': [handle, wide, uint, handle, uint],
            'ORGetValue': [handle, wide, wide, pointer(uint), handle, pointer(uint)],
            'ORSaveHive': [handle, wide, uint, uint],
        }.items():
            function = getattr(lib, name)
            function.argtypes, function.restype = args, uint
        return lib

    def create_hive(self, path, invalid_marker=False):
        lib = self.native(); root=C.c_void_p(); key=C.c_void_p(); empty=C.c_void_p(); disposition=C.c_uint32()
        self.assertEqual(lib.ORCreateHive(C.byref(root)), 0)
        try:
            self.assertEqual(lib.ORCreateKey(root, 'Description', None, 0, None, C.byref(key), C.byref(disposition)), 0)
            data=C.create_string_buffer(b'opaque\x00bytes\xff')
            self.assertEqual(lib.ORSetValue(key, 'PreserveMe', 3, data, len(data.raw)), 0)
            if invalid_marker:
                value=C.create_unicode_buffer('wrong type')
                self.assertEqual(lib.ORSetValue(key, 'System', 1, value, C.sizeof(value)), 0)
            self.assertEqual(lib.ORCreateKey(root, 'EmptyKey', None, 0, None, C.byref(empty), C.byref(disposition)), 0)
            self.assertEqual(lib.ORSaveHive(root, str(path), 6, 1), 0)
        finally:
            if key:self.assertEqual(lib.ORCloseKey(key), 0)
            if empty:self.assertEqual(lib.ORCloseKey(empty), 0)
            self.assertEqual(lib.ORCloseHive(root), 0)

    def test_offline_marker_preserves_opaque_values_and_empty_keys(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            source=Path(temporary)/'source.hiv'; output=Path(temporary)/'output.hiv'
            self.create_hive(source); before=hashlib.sha256(source.read_bytes()).hexdigest()
            result=self.invoke('Write-GuestSystemMarker $Source $Output; @{written=(Test-Path -LiteralPath $Output)}|ConvertTo-Json -Compress', str(source), str(output))
            self.assertTrue(result['written']); self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
            lib=self.native(); root=C.c_void_p(); empty=C.c_void_p()
            self.assertEqual(lib.OROpenHive(str(output), C.byref(root)), 0)
            try:
                data=C.create_string_buffer(64); kind=C.c_uint32(); size=C.c_uint32(64)
                self.assertEqual(lib.ORGetValue(root, 'Description', 'PreserveMe', C.byref(kind), data, C.byref(size)), 0)
                self.assertEqual((kind.value,data.raw[:size.value]), (3,b'opaque\x00bytes\xff\x00'))
                size.value=64
                self.assertEqual(lib.ORGetValue(root, 'Description', 'System', C.byref(kind), data, C.byref(size)), 0)
                self.assertEqual((kind.value,data.raw[:size.value]), (4,b'\x01\x00\x00\x00'))
                self.assertEqual(lib.OROpenKey(root, 'EmptyKey', C.byref(empty)), 0)
            finally:
                if empty:self.assertEqual(lib.ORCloseKey(empty), 0)
                self.assertEqual(lib.ORCloseHive(root), 0)

    def test_invalid_marker_and_existing_output_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            source=Path(temporary)/'source.hiv'; output=Path(temporary)/'output.hiv'
            self.create_hive(source, invalid_marker=True)
            result=self.invoke("$rejected=$false;try{Write-GuestSystemMarker $Source $Output}catch{$rejected=$true};@{rejected=$rejected;outputExists=(Test-Path -LiteralPath $Output)}|ConvertTo-Json -Compress", str(source), str(output))
            self.assertEqual(result, {'rejected': True, 'outputExists': False})
            output.write_bytes(b'keep'); before=source.read_bytes()
            result=self.invoke("$rejected=$false;try{Write-GuestSystemMarker $Source $Output}catch{$rejected=$true};@{rejected=$rejected}|ConvertTo-Json -Compress", str(source), str(output))
            self.assertTrue(result['rejected']); self.assertEqual(output.read_bytes(), b'keep'); self.assertEqual(source.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
