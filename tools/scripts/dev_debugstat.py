#!/usr/bin/env python3
"""Read MTK i2c DEBUGSTAT registers via /dev/mem to inspect SCL/SDA levels."""
import mmap, os, struct, sys

BASES = {
    "i2c0/11007000": 0x11007000,
    "i2c1/11008000": 0x11008000,
    "i2c2/11009000": 0x11009000,
    "i2c3/1100f000": 0x1100f000,
    "i2c4/11011000": 0x11011000,
    "i2c5/11016000": 0x11016000,
    "i2c6/1100d000": 0x1100d000,
}

fd = os.open("/dev/mem", os.O_RDONLY | os.O_SYNC)
for name, base in BASES.items():
    off = base & ~0xfff
    try:
        m = mmap.mmap(fd, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ, offset=off)
    except OSError as e:
        print("%-16s mmap failed: %s" % (name, e)); continue
    d = base - off
    v64 = struct.unpack_from("<I", m, d + 0x64)[0]
    ve4 = struct.unpack_from("<I", m, d + 0xe4)[0]
    print("%-16s DEBUGSTAT@0x64=0x%08x  @0xe4=0x%08x" % (name, v64, ve4))
    m.close()
os.close(fd)
