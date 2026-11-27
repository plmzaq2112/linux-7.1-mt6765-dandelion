#!/usr/bin/env python3
import os, struct, glob, sys

d = sys.argv[1] if len(sys.argv) > 1 else "logs/pvr-maps2"
files = sorted(glob.glob(os.path.join(d, "pvr-map-*.bin")))
pat64 = struct.pack("<f", 64.0)
pat32 = struct.pack("<f", 32.0)
pats = {
    "f64": pat64,
    "f32": pat32,
    "pds0": struct.pack("<I", 0x0009c000),
    "pds1": struct.pack("<I", 0x0009c200),
    "evt": struct.pack("<I", 0x004dc000),
    "vdm": struct.pack("<I", 0x0018b000),
    "red": struct.pack("<I", 0xff0000ff),
}

for f in files:
    data = open(f, "rb").read()
    nz = sum(1 for b in data if b)
    hits = {}
    for name, pat in pats.items():
        offs = [i for i in range(0, len(data) - len(pat) + 1) if data[i:i+len(pat)] == pat]
        if offs:
            hits[name] = offs[:6]
    if not hits and nz < 64:
        continue
    print(os.path.basename(f), "size", len(data), "nz", nz, hits)
    if nz and (hits or len(data) <= 4096):
        print("  head:", data[:128].hex())
