#!/usr/bin/env python3
"""Search the SCP firmware for MT6765 i2c controller base addresses."""
import struct, sys

raw = open("/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/scp2.bin", "rb").read()
print("size", len(raw))

bases = {
    0x11007000: "i2c0", 0x11008000: "i2c1", 0x11009000: "i2c2",
    0x1100F000: "i2c3", 0x11011000: "i2c4", 0x11016000: "i2c5",
    0x1100D000: "i2c6",
}

for addr, name in bases.items():
    pat = struct.pack("<I", addr)
    hits = []
    i = raw.find(pat)
    while i != -1 and len(hits) < 8:
        hits.append(i)
        i = raw.find(pat, i + 1)
    print("%s 0x%08x: %d hits %s" % (name, addr, len(hits), [hex(h) for h in hits]))

# also search the 0x1100xxxx page for any 0x1100?000 word
print("\n-- all 0x1100X000 words --")
seen = {}
for off in range(0, len(raw) - 4):
    v = struct.unpack_from("<I", raw, off)[0]
    if 0x11000000 <= v <= 0x1101FFFF and (v & 0xFFF) == 0:
        seen.setdefault(v, []).append(off)
for v, offs in sorted(seen.items()):
    print("0x%08x x%d @ %s" % (v, len(offs), [hex(o) for o in offs[:5]]))
