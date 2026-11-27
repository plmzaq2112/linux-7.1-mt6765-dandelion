#!/usr/bin/env python3
"""stable21: give i2c2/4/6 their per-instance clocks via the driver's "arb" slot.

i2c2: CLK_IFR_I2C2_IMM  (47 = 0x2f)  (ARBITER=46 already failed)
i2c4: CLK_IFR_I2C4      (38 = 0x26)
i2c6: CLK_IFR_I2C6      (54 = 0x36)
"""
import struct, subprocess, os

W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
SRC = W + "/rootfs/ubuntu/boot/images/boot-stable19-i2carb.img"
DST = W + "/rootfs/ubuntu/boot/images/boot-stable21-i2cclk.img"
WORK = W + "/logs/repack21"
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

def set_clocks(node, clock_list):
    global text
    i = text.find(node + " {")
    assert i > 0, node
    j = text.find("clocks = ", i)
    k = text.find(";", j) + 1
    assert 0 < j < i + 3000 and k > j
    text = text[:j] + "clocks = <%s>;" % clock_list + text[k:]

def set_names(node, names):
    global text
    i = text.find(node + " {")
    j = text.find("clock-names = ", i)
    k = text.find(";", j) + 1
    assert 0 < j < i + 3000
    text = text[:j] + 'clock-names = "main", "dma", "arb";' + text[k:]

BASE = "0x16 0x04 0x16 0x1c"
# i2c2: replace ARBITER(0x2e) with IMM(0x2f)
set_clocks("i2c@11009000", BASE + " 0x16 0x2f")
set_names("i2c@11009000", "main, dma, arb")
# i2c4 / i2c6: add their own gate
set_clocks("i2c@11011000", BASE + " 0x16 0x26")
set_names("i2c@11011000", "main, dma, arb")
set_clocks("i2c@1100d000", BASE + " 0x16 0x36")
set_names("i2c@1100d000", "main, dma, arb")

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
