#!/usr/bin/env python3
import struct, subprocess, os

W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
IMG = W + "/rootfs/ubuntu/boot/images/boot-stable11-pwm.img"
WORK = "/tmp/verify11"
os.makedirs(WORK, exist_ok=True)
d = open(IMG, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
off = page + au(ks, page) + au(rs, page)
open(WORK + "/x.dtb", "wb").write(d[off:off+ds])
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", WORK + "/x.dts", WORK + "/x.dtb"],
               check=True, stderr=subprocess.DEVNULL)
t = open(WORK + "/x.dts").read()
print("phandle 0x140 count:", t.count("phandle = <0x140>"))
print("pinmux 0x2b01 count:", t.count("pinmux = <0x2b01>"))
i = t.find("pwm@1100e000")
print(t[i:i+420])
