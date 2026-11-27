#!/usr/bin/env python3
import struct, subprocess, os
W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
IMG = W + "/rootfs/ubuntu/boot/images/boot-stable19-i2carb.img"
OUT = W + "/logs/v19"
os.makedirs(OUT, exist_ok=True)
d = open(IMG, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
off = page + au(ks, page) + au(rs, page)
open(OUT + "/v19.dtb", "wb").write(d[off:off+ds])
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", OUT + "/v19.dts", OUT + "/v19.dtb"],
               check=True, stderr=subprocess.DEVNULL)
t = open(OUT + "/v19.dts").read()
for node in ("i2c@11008000", "i2c@11009000", "i2c@11016000"):
    i = t.find(node)
    print("--", node)
    print(t[i:i+260])
print("vibrator node:", "regulator-vibrator" in t)
print("kernel", ks, "dtb", ds)
