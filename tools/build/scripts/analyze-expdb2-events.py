#!/usr/bin/env python3
"""List LK boot events in expdb2.bin in offset order."""
import re

p = ("/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
     "logs/device/recovery-pstore-2026-11-19/expdb2.bin")
d = open(p, "rb").read()

patterns = [
    (rb"kedump: current time: \[[^\]]*\]", "TIME"),
    (rb"load (?:boot|recovery) image takes \d+ ms", "LOAD"),
    (rb"booting linux @ [0-9a-fx]+, ramdisk @ [0-9a-fx]+ \(\d+\)", "JUMP"),
    (rb"kernel real kernel_sz=0x[0-9a-f]+", "KSZ"),
    (rb"decompress_kernel takes \d+ ms", "DECOMP"),
    (rb"panics? \(caller[^\n]*", "PANIC"),
    (rb"ASSERT at [^\n]*", "ASSERT"),
    (rb"boot image dtb_overlay fail", "OVLFAIL"),
    (rb"\[avb\] cmdline = [^\n]*", "AVBCMD"),
    (rb"reboot: Restarting system[^\n]*", "REBOOT"),
    (rb"[0-9a-f]{8} b13ae8|b13ae8", "OURKSZ"),
]

ev = []
for pat, tag in patterns:
    for m in re.finditer(pat, d):
        ev.append((m.start(), tag, m.group(0).decode("latin1")[:150]))
ev.sort()

for off, tag, txt in ev:
    print("%9d %-8s %s" % (off, tag, txt))
