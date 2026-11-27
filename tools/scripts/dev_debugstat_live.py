#!/usr/bin/env python3
"""Sample i2c DEBUGSTAT while transfers are running (clocks on)."""
import mmap, os, struct, time, sys

base = int(sys.argv[1], 0)
off = base & ~0xfff
fd = os.open("/dev/mem", os.O_RDONLY | os.O_SYNC)
m = mmap.mmap(fd, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ, offset=off)
d = base - off
seen = {}
for _ in range(120):
    v64 = struct.unpack_from("<I", m, d + 0x64)[0]
    ve4 = struct.unpack_from("<I", m, d + 0xe4)[0]
    if v64 or ve4:
        seen[(v64, ve4)] = seen.get((v64, ve4), 0) + 1
    time.sleep(0.1)
for (a, b), n in seen.items():
    print("0x64=0x%08x 0xe4=0x%08x  x%d" % (a, b, n))
if not seen:
    print("all samples zero (clock gated)")
m.close()
os.close(fd)
