import os
import re
import struct
import subprocess

SRC = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/images/boot-stable1.img"
DST = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/images/boot-stable2.img"
WORK = "/tmp/stable2"
os.makedirs(WORK, exist_ok=True)

d = open(SRC, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
k_off = page
rd_off = k_off + au(ks, page)
dt_off = rd_off + au(rs, page)
kernel = d[k_off:k_off + ks]
ramdisk = d[rd_off:rd_off + rs]
dtb = d[dt_off:dt_off + ds]

open(WORK + "/base.dtb", "wb").write(dtb)
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", WORK + "/base.dtb",
                "-o", WORK + "/base.dts"], check=True, stderr=subprocess.DEVNULL)
text = open(WORK + "/base.dts").read()

m = re.search(r'(\n\t*audio-controller \{)(.*?)(\n\t*\};)', text, re.S)
assert m, "afe node not found"
body = m.group(2)
print("--- afe before ---")
print(body[:400])

new_body, n = re.subn(r'interrupts = <0x00 0x99 0x04>;',
                      'interrupts = <0x00 0x99 0x08>;', body)
print("interrupt type changed:", n)
assert n == 1
text = text[:m.start(2)] + new_body + text[m.end(2):]
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
