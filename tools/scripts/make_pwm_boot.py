#!/usr/bin/env python3
import os, struct, subprocess

W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
SRC = W + "/rootfs/ubuntu/boot/images/boot-stable10-bright.img"
DST = W + "/rootfs/ubuntu/boot/images/boot-stable11-pwm.img"
WORK = "/tmp/pwmpin"
os.makedirs(WORK, exist_ok=True)

d = open(SRC, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
kernel = d[page:page + ks]
rd_off = page + au(ks, page)
ramdisk = d[rd_off:rd_off + rs]
dt_off = rd_off + au(rs, page)
dtb = d[dt_off:dt_off + ds]

open(WORK + "/base.dtb", "wb").write(dtb)
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", WORK + "/base.dts",
                WORK + "/base.dtb"], check=True, stderr=subprocess.DEVNULL)
text = open(WORK + "/base.dts").read()

# 1) pinctrl state for GPIO43 func 1 (DISP_PWM)
anchor = None
for cand in ("\t\t\tphandle = <0x10>;\n",):
    if text.count(cand) == 1:
        anchor = cand
assert anchor, "pin-controller phandle anchor not unique/found"

state = """\n\t\t\tdisp-pwm-pins {
\t\t\t\tphandle = <0x140>;

\t\t\t\tpins {
\t\t\t\t\tpinmux = <0x2b01>;
\t\t\t\t};
\t\t\t};
"""
text = text.replace(anchor, anchor + state, 1)

# 2) attach pinctrl to the disp pwm node
old = """\t\tpwm@1100e000 {
\t\t\tcompatible = "mediatek,mt6765-disp-pwm", "mediatek,mt8183-disp-pwm";"""
new = """\t\tpwm@1100e000 {
\t\t\tcompatible = "mediatek,mt6765-disp-pwm", "mediatek,mt8183-disp-pwm";
\t\t\tpinctrl-0 = <0x140>;
\t\t\tpinctrl-names = "default";"""
assert text.count(old) == 1
text = text.replace(old, new, 1)

open(WORK + "/new.dts", "w").write(text)
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", WORK + "/new.dtb",
                WORK + "/new.dts"], check=True, stderr=subprocess.DEVNULL)
newdtb = open(WORK + "/new.dtb", "rb").read()
print("dtb", len(dtb), "->", len(newdtb))

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
