# Dumps the running game's main module (as mapped in memory: file offset = RVA) to a file.
# Read-only: OpenProcess with query + VM read rights, ReadProcessMemory per committed region.
# Usage: python dumpimage.py LIS2-Win64-Shipping.exe out.bin
import ctypes
import ctypes.wintypes as wt
import struct
import sys

PROCESS_QUERY_INFORMATION, PROCESS_VM_READ = 0x0400, 0x0010
MEM_COMMIT, PAGE_NOACCESS, PAGE_GUARD = 0x1000, 0x01, 0x100
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                                  ctypes.POINTER(ctypes.c_size_t)]
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
k32.VirtualQueryEx.restype = ctypes.c_size_t


class MBI(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wt.DWORD), ('PartitionId', wt.WORD), ('RegionSize', ctypes.c_size_t),
                ('State', wt.DWORD), ('Protect', wt.DWORD), ('Type', wt.DWORD)]


def find_pid(name):
    pids = (wt.DWORD * 4096)()
    got = wt.DWORD()
    psapi.EnumProcesses(pids, ctypes.sizeof(pids), ctypes.byref(got))
    for pid in pids[:got.value // 4]:
        h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not h:
            continue
        buf = ctypes.create_unicode_buffer(260)
        if psapi.GetModuleBaseNameW(h, None, buf, 260) and buf.value.lower() == name.lower():
            return pid, h
        k32.CloseHandle(h)
    sys.exit('process not found: ' + name)


def read(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t()
    if not k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)):
        return None
    return buf.raw[:n.value]


pid, h = find_pid(sys.argv[1])
mods = (ctypes.c_void_p * 1024)()
need = wt.DWORD()
psapi.EnumProcessModulesEx(h, mods, ctypes.sizeof(mods), ctypes.byref(need), 3)
base = mods[0]
hdr = read(h, base, 0x1000)
pe = struct.unpack_from('<I', hdr, 0x3c)[0]
size = struct.unpack_from('<I', hdr, pe + 24 + 56)[0]  # SizeOfImage
print('pid %d base %#x image size %d MB' % (pid, base, size >> 20))
out = bytearray(size)
addr, end, copied = base, base + size, 0
while addr < end:
    mbi = MBI()
    if not k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    region_end = min(mbi.BaseAddress + mbi.RegionSize, end)
    readable = mbi.State == MEM_COMMIT and not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD))
    a = addr
    while readable and a < region_end:
        chunk = min(1 << 20, region_end - a)
        data = read(h, a, chunk)
        if data:
            out[a - base:a - base + len(data)] = data
            copied += len(data)
        a += chunk
    addr = region_end
open(sys.argv[2], 'wb').write(out)
print('wrote %s, %d MB readable' % (sys.argv[2], copied >> 20))
