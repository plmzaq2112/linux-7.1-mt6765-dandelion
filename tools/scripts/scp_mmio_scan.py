#!/usr/bin/env python3
"""List page-aligned MMIO-looking words in the SCP firmware."""
import struct
from collections import Counter

raw = open("/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/scp2.bin", "rb").read()
c = Counter()
for off in range(0, len(raw) - 4, 4):
    v = struct.unpack_from("<I", raw, off)[0]
    if 0x10000000 <= v <= 0x1FFFFFFF and (v & 0xFFF) == 0:
        c[v] += 1
for v, n in c.most_common(40):
    print("0x%08x x%d" % (v, n))

print("\n-- GPIO/APB strings --")
for s in (b"gpio", b"GPIO", b"i2c", b"I2C", b"alsps", b"stk3x", b"sc7a"):
    print(s, raw.count(s))
