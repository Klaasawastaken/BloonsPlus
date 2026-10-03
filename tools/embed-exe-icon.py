"""Embed the Bloons+ icon into a staged executable, before packaging/signing.

Uses Windows BeginUpdateResource/UpdateResource; preserves non-icon resources.
Never run this against a live application or the vendor's original runtime.
"""
import ctypes
from ctypes import wintypes
from pathlib import Path
import struct
import sys

def embed(executable, icon):
    executable = Path(executable).resolve()
    data = Path(icon).read_bytes()
    reserved, kind, count = struct.unpack_from('<HHH', data)
    if reserved or kind != 1 or not count:
        raise ValueError('Invalid ICO header')
    images = []
    group = bytearray(data[:6])
    for index in range(count):
        width, height, colors, zero, planes, bits, length, offset = struct.unpack_from('<BBBBHHII', data, 6 + index * 16)
        pixels = data[offset:offset + length]
        if len(pixels) != length:
            raise ValueError('Truncated ICO image')
        images.append(pixels)
        group.extend(struct.pack('<BBBBHHIH', width, height, colors, zero, planes, bits, length, index + 1))
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    begin = kernel.BeginUpdateResourceW
    begin.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
    begin.restype = wintypes.HANDLE
    update = kernel.UpdateResourceW
    update.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, wintypes.WORD, ctypes.c_void_p, wintypes.DWORD]
    update.restype = wintypes.BOOL
    end = kernel.EndUpdateResourceW
    end.argtypes = [wintypes.HANDLE, wintypes.BOOL]
    end.restype = wintypes.BOOL
    handle = begin(str(executable), False)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        # Electron's primary group is 1. Replace both neutral and English forms
        # so Windows does not choose the original Electron icon by locale.
        for language in (0, 1033):
            for index, pixels in enumerate(images, 1):
                buffer = ctypes.create_string_buffer(pixels)
                if not update(handle, 3, index, language, buffer, len(pixels)):
                    raise ctypes.WinError(ctypes.get_last_error())
            buffer = ctypes.create_string_buffer(bytes(group))
            if not update(handle, 14, 1, language, buffer, len(group)):
                raise ctypes.WinError(ctypes.get_last_error())
    except BaseException:
        end(handle, True)
        raise
    if not end(handle, False):
        raise ctypes.WinError(ctypes.get_last_error())

if __name__ == '__main__':
    embed(*sys.argv[1:])
