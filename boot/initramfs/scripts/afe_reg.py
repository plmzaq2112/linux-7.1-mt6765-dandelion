#!/usr/bin/env python3
"""Read/modify the audsys/AFE registers via /dev/mem.

usage:
  afe_reg.py read [off]   -> print register at 0x11220000+off
  afe_reg.py on           -> clear PDN_AFE (bit 2 of AUDIO_TOP_CON0)
"""
import mmap
import os
import sys

BASE = 0x11220000
PDN_AFE = 1 << 2

fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
page = mmap.mmap(fd, 0x4000, mmap.MAP_SHARED,
                 mmap.PROT_READ | mmap.PROT_WRITE, offset=BASE)


def rd(off):
    return int.from_bytes(page[off:off + 4], "little")


def wr(off, v):
    page[off:off + 4] = v.to_bytes(4, "little")


cmd = sys.argv[1] if len(sys.argv) > 1 else "read"
if cmd == "read":
    offs = [int(x, 0) for x in sys.argv[2:]] or [0]
    for o in offs:
        print("0x%08x: 0x%08x" % (BASE + o, rd(o)))
elif cmd == "on":
    before = rd(0)
    wr(0, before & ~PDN_AFE)
    print("before 0x%08x -> after 0x%08x" % (before, rd(0)))
page.close()
os.close(fd)
