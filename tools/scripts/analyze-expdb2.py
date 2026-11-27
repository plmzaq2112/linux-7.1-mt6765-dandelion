#!/usr/bin/env python3
"""Compare boot attempts in the latest expdb dump (expdb2.bin)."""
import re
import sys

p = ("/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
     "logs/device/recovery-pstore-2026-11-19/expdb2.bin")
d = open(p, "rb").read()

keys = [b"load boot image takes", b"load recovery image takes", b"booting linux @",
        b"dtb_overlay fail", b"fdt_bootargs", b"ufdt_apply_overlay() failed",
        b"__symbols__", b"jump to linux kernel", b"kernel_sz", b"decompress_kernel"]
for k in keys:
    idx = [m.start() for m in re.finditer(re.escape(k), d)]
    print("%-32s count=%d last=%s" % (k.decode(), len(idx), idx[-4:]))

print("\n=== tail 2500 chars (decoded) ===")
print(d[-2500:].decode("latin1"))

print("\n=== last 'booting linux' context ===")
idx = [m.start() for m in re.finditer(re.escape(b"booting linux @"), d)]
for o in idx[-1:]:
    print(d[max(0, o - 1500):o + 300].decode("latin1"))
