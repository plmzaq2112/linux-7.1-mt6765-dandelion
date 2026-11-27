#!/usr/bin/env python3
"""Find the newest LK boot records in expdb2.bin via 'kedump: current time' markers."""
import re

p = ("/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
     "logs/device/recovery-pstore-2026-11-19/expdb2.bin")
d = open(p, "rb").read()

ms = [(m.start(), m.group(0).decode("latin1")) for m in
      re.finditer(rb"kedump: current time: \[[^\]]*\]", d)]
print("boot time markers (%d):" % len(ms))
for o, t in ms:
    print("  off=%d  %s" % (o, t))

# biggest zero run tells us where the ring writer currently is
runs = [(m.start(), m.end() - m.start()) for m in re.finditer(rb"\x00{4096,}", d)]
print("\nzero runs >=4K (first 5):")
for s, l in runs[:5]:
    print("  off=%d len=%d" % (s, l))
if runs:
    s, l = max(runs, key=lambda x: x[1])
    print("\nlargest zero run off=%d len=%d -> data just before it:" % (s, l))
    print(d[max(0, s - 3000):s].decode("latin1"))

print("\n=== head 1500 chars ===")
print(d[:1500].decode("latin1"))
