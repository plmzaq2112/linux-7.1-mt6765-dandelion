#!/usr/bin/env python3
"""Dump MTK i2c controller registers for i2c3 (broken) and i2c5 (working)."""
import mmap
import os

BASE3 = 0x1100f000
BASE5 = 0x11016000

fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)


def dump(base):
    page = mmap.mmap(fd, 0x1000, mmap.MAP_SHARED,
                     mmap.PROT_READ | mmap.PROT_WRITE, offset=base)
    print("=== 0x%08x" % base)
    for off in range(0, 0x40, 4):
        v = int.from_bytes(page[off:off + 4], "little")
        print(" 0x%02x: 0x%08x" % (off, v))
    page.close()


dump(BASE3)
dump(BASE5)
os.close(fd)
