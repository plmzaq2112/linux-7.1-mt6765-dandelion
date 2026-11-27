#!/usr/bin/env python3
import struct, subprocess, os
W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
IMG = W + "/rootfs/ubuntu/boot/images/boot-stable18-vibr.img"
OUT = W + "/logs/v18"
os.makedirs(OUT, exist_ok=True)
d = open(IMG, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
off = page + au(ks, page) + au(rs, page)
open(OUT + "/v18.dtb", "wb").write(d[off:off+ds])
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", OUT + "/v18.dts", OUT + "/v18.dtb"],
               check=True, stderr=subprocess.DEVNULL)
t = open(OUT + "/v18.dts").read()
i = t.find("regulator-vibrator")
print(t[max(0, i-120):i+320] if i > 0 else "NOT FOUND")
print("kernel", ks, "dtb", ds)
