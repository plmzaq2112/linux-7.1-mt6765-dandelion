import os
import re
import struct
import subprocess

SRC = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/images/boot-stable2.img"
DST = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/images/boot-stable3.img"
WORK = "/tmp/stable3"
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

old_clocks = re.search(r'clocks = <(.*?)>;', body, re.S).group(1)
print("clocks before ends with:", old_clocks.strip()[-20:])
new_clocks = old_clocks.rstrip() + " 0xac 0x00"
body2 = body.replace("clocks = <" + old_clocks + ">;",
                     "clocks = <" + new_clocks + ">;", 1)

old_names = re.search(r'clock-names = "(.*?)";', body, re.S).group(0)
new_names = old_names.replace('";', '", "aud_afe";')
body2 = body2.replace(old_names, new_names, 1)
assert "aud_afe" in body2
print("clock-names now ends with:", new_names[-40:])

text = text[:m.start(2)] + body2 + text[m.end(2):]
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
