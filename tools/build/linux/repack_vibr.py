#!/usr/bin/env python3
"""Add a regulator-vibrator node to the boot DTB and repack as stable18."""
import struct, subprocess, os

W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
SRC = W + "/rootfs/ubuntu/boot/images/boot-stable17-panelbl2047.img"
DST = W + "/rootfs/ubuntu/boot/images/boot-stable18-vibr.img"
WORK = W + "/logs/repack18"
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

if "regulator-vibrator" not in text:
    node = """
	vibrator {
		compatible = "regulator-vibrator";
		vib-supply = <0x8f>;
		min-volt = <0x1e8480>;
		max-volt = <0x2dc6c0>;
		min-limit = <0x0f>;
		max-limit = <0x3a98>;
	};
"""
    stripped = text.rstrip()
    assert stripped.endswith("};"), stripped[-20:]
    text = stripped[:-2] + node + "};\n"

open(WORK + "/new.dts", "w").write(text)
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", WORK + "/new.dtb", WORK + "/new.dts"],
               check=True, stderr=subprocess.DEVNULL)
newdtb = open(WORK + "/new.dtb", "rb").read()
print("dtb", len(dtb), "->", len(newdtb))

kernel = d[page:page + ks]
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
