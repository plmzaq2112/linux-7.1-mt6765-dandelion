#!/usr/bin/env python3
import struct, subprocess, os
W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
IMG = W + "/rootfs/ubuntu/boot/images/boot-stable17-panelbl2047.img"
OUT = W + "/logs/v17"
os.makedirs(OUT, exist_ok=True)
d = open(IMG, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
off = page + au(ks, page) + au(rs, page)
open(OUT + "/v17.dtb", "wb").write(d[off:off+ds])
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", OUT + "/v17.dts", OUT + "/v17.dtb"],
               check=True, stderr=subprocess.DEVNULL)
t = open(OUT + "/v17.dts").read()
i = t.find("vibrator@0")
print("---- vibrator node ----")
print(t[max(0, i-200):i+400])
j = t.find("ldo-vibr")
print("---- ldo-vibr node ----")
print(t[j-100:j+500])
print("kernel", ks, "dtb", ds)
