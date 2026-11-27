#!/usr/bin/env python3
"""stable20: disable hw i2c 2/3/4/6 and add i2c-gpio buses on the same pins.

SCP firmware uses the AP i2c controllers (i2cchre-plat.c); if the controller is
left in a state the AP cannot drive, bit-banging the same pins is the way in.
"""
import struct, subprocess, os, re

W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
SRC = W + "/rootfs/ubuntu/boot/images/boot-stable19-i2carb.img"
DST = W + "/rootfs/ubuntu/boot/images/boot-stable20-i2cgpio.img"
WORK = W + "/logs/repack20"
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
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", WORK + "/base.dts", WORK + "/base.dtb"],
               check=True, stderr=subprocess.DEVNULL)
text = open(WORK + "/base.dts").read()

BUSES = [
    ("i2c@11009000", 103, 104, "i2c_gpio2"),
    ("i2c@1100f000", 50, 51, "i2c_gpio3"),
    ("i2c@11011000", 105, 106, "i2c_gpio4"),
    ("i2c@1100d000", 161, 162, "i2c_gpio6"),
]

PIO = 0x10  # pio phandle in this DTB

for node, scl, sda, label in BUSES:
    i = text.find(node + " {")
    assert i > 0, node
    j = text.find('status = "okay";', i)
    assert 0 < j < i + 4000, (node, j)
    text = text[:j] + 'status = "disabled";' + text[j + len('status = "okay";'):]

nodes = ""
for node, scl, sda, label in BUSES:
    nodes += """
	%s {
		compatible = "i2c-gpio";
		scl-gpios = <0x%x %d 0x02>;
		sda-gpios = <0x%x %d 0x02>;
		i2c-gpio,delay-us = <0x05>;
		#address-cells = <0x01>;
		#size-cells = <0x00>;
	};
""" % (label, PIO, scl, PIO, sda)

stripped = text.rstrip()
assert stripped.endswith("};")
text = stripped[:-2] + nodes + "};\n"

open(WORK + "/new.dts", "w").write(text)
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", WORK + "/new.dtb", WORK + "/new.dts"],
               check=True, stderr=subprocess.DEVNULL)
newdtb = open(WORK + "/new.dtb", "rb").read()
print("dtb", len(dtb), "->", len(newdtb))

kernel = d[page:page + ks]
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
