#!/usr/bin/env python3
"""stable22: bit-bang i2c0/i2c1 too (50 kHz), keep i2c5 as hardware (charger)."""
import struct, subprocess, os

W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
SRC = W + "/rootfs/ubuntu/boot/images/boot-stable21-i2cclk.img"
DST = W + "/rootfs/ubuntu/boot/images/boot-stable22-i2c01gpio.img"
WORK = W + "/logs/repack22"
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
    ("i2c@11007000", 83, 82, "i2c_gpio0"),   # SCL0=83, SDA0=82
    ("i2c@11008000", 84, 81, "i2c_gpio1"),   # SCL1=84, SDA1=81
]

for node, scl, sda, label in BUSES:
    i = text.find(node + " {")
    assert i > 0, node
    j = text.find('status = "okay";', i)
    assert 0 < j < i + 4000, node
    text = text[:j] + 'status = "disabled";' + text[j + len('status = "okay";'):]

nodes = ""
for node, scl, sda, label in BUSES:
    nodes += """
	%s {
		compatible = "i2c-gpio";
		scl-gpios = <0x10 %d 0x02>;
		sda-gpios = <0x10 %d 0x02>;
		i2c-gpio,delay-us = <0x0a>;
		#address-cells = <0x01>;
		#size-cells = <0x00>;
	};
""" % (label, scl, sda)

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
