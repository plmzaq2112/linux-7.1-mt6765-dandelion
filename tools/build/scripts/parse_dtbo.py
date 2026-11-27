#!/usr/bin/env python3
import struct, subprocess, os, sys

p = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/dtbo.img"
d = open(p, "rb").read()
magic, total, hsize, esize, ecnt, eoff = struct.unpack_from(">IIIIII", d, 0)
print("magic=%08x total=%d hsize=%d esize=%d count=%d eoff=%d" % (magic, total, hsize, esize, ecnt, eoff))
os.makedirs("/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/dtbo", exist_ok=True)
for i in range(ecnt):
    sz, off, id_, rev = struct.unpack_from(">IIII", d, eoff + i * esize)
    blob = d[off:off + sz]
    out = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/dtbo/%d.dtb" % i
    open(out, "wb").write(blob)
    print("entry %d size=%d off=%d id=%d" % (i, sz, off, id_))
    subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o",
                    "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/dtbo/%d.dts" % i, out],
                   stderr=subprocess.DEVNULL)
    print("  wrote dts %d" % i)
