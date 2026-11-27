#!/usr/bin/env python3
import os, struct, glob

d = os.path.join(os.path.dirname(__file__), "..", "logs", "pvr-maps")
files = sorted(glob.glob(os.path.join(d, "pvr-map-*.bin")))
pat64 = struct.pack("<f", 64.0)
pat32 = struct.pack("<f", 32.0)

for f in files:
    data = open(f, "rb").read()
    nz = sum(1 for b in data if b)
    hits64 = [i for i in range(0, len(data) - 3) if data[i:i+4] == pat64]
    hits32 = [i for i in range(0, len(data) - 3) if data[i:i+4] == pat32]
    if nz == 0 and not hits64 and not hits32:
        continue
    print(os.path.basename(f), "size", len(data), "nonzero_bytes", nz,
          "f64", hits64[:8], "f32", hits32[:8])
    if nz:
        chunk = data[:min(128, len(data))]
        print("  head:", chunk.hex())
