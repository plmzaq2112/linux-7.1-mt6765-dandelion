#!/usr/bin/env python3
"""stable19: add the SCP i2c arbiter clock to i2c1/i2c2/i2c5 (keeps vibrator node)."""
import struct, subprocess, os

W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
SRC = W + "/rootfs/ubuntu/boot/images/boot-stable18-vibr.img"
DST = W + "/rootfs/ubuntu/boot/images/boot-stable19-i2carb.img"
WORK = W + "/logs/repack19"
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

OLD_CLK = "\t\t\tclocks = <0x16 0x04 0x16 0x1c>;\n\t\t\tclock-names = \"main\", \"dma\";\n"
NEW_CLK = "\t\t\tclocks = <0x16 0x04 0x16 0x1c 0x16 0x2e>;\n\t\t\tclock-names = \"main\", \"dma\", \"arb\";\n"

for node in ("i2c@11008000", "i2c@11009000", "i2c@11016000"):
    i = text.find(node + " {")
    assert i > 0, node
    j = text.find(OLD_CLK, i)
    assert 0 < j < i + 3000, (node, j)
    text = text[:j] + NEW_CLK + text[j + len(OLD_CLK):]

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
