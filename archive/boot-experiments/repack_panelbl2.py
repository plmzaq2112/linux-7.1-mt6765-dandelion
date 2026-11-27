#!/usr/bin/env python3
"""Repack boot: new Image.gz + DTB with pwm-backlight disabled (panel owns backlight)."""
import os, struct, subprocess

W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
T = "/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline"
SRC = W + "/rootfs/ubuntu/boot/images/boot-stable11-pwm.img"
DST = W + "/rootfs/ubuntu/boot/images/boot-stable14-panelbl2.img"
KERNEL = T + "/out/arch/arm64/boot/Image.gz"
WORK = "/tmp/repack14"
os.makedirs(WORK, exist_ok=True)

d = open(SRC, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
rd_off = page + au(ks, page)
ramdisk = d[rd_off:rd_off + rs]
dt_off = rd_off + au(rs, page)
dtb = d[dt_off:dt_off + ds]

open(WORK + "/base.dtb", "wb").write(dtb)
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", WORK + "/base.dts",
                WORK + "/base.dtb"], check=True, stderr=subprocess.DEVNULL)
text = open(WORK + "/base.dts").read()
old = """\tbacklight {
\t\tcompatible = "pwm-backlight";
\t\tpwms = <0xa3 0x00 0x186a0>;
\t\tbrightness-levels = <0x00 0x04 0x08 0x10 0x20 0x40 0x60 0x80 0xa0 0xc0 0xe0 0xff>;
\t\tnum-interpolated-steps = <0x08>;
\t\tdefault-brightness-level = <0x0a>;
\t\tenable-gpios = <0x10 0x9a 0x00>;
\t};"""
new = old[:-3] + "\t\tstatus = \"disabled\";\n\t};"
assert text.count(old) == 1, text.count(old)
text = text.replace(old, new, 1)
open(WORK + "/new.dts", "w").write(text)
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", WORK + "/new.dtb",
                WORK + "/new.dts"], check=True, stderr=subprocess.DEVNULL)
newdtb = open(WORK + "/new.dtb", "rb").read()
print("dtb", len(dtb), "->", len(newdtb))

kernel = open(KERNEL, "rb").read()
print("kernel", len(kernel))

hdr = bytearray(d[:page])
struct.pack_into("<I", hdr, 8, len(kernel))
struct.pack_into("<I", hdr, 16, len(ramdisk))
struct.pack_into("<I", hdr, 24, 0)
if hv >= 2:
    struct.pack_into("<I", hdr, 1648, len(newdtb))

buf = bytearray()
buf += hdr
buf += kernel
buf += b"\x00" * (au(len(buf), page) - len(buf))
buf += ramdisk
buf += b"\x00" * (au(len(buf), page) - len(buf))
buf += newdtb
buf += b"\x00" * (au(len(buf), page) - len(buf))
if len(buf) < len(d):
    buf += b"\x00" * (len(d) - len(buf))
open(DST, "wb").write(buf)
print("wrote", DST, len(buf))
