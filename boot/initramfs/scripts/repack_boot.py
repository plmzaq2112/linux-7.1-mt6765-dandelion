import struct, os, json

OUT = "/tmp/db"
DST = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-debug.img"

meta = json.load(open(os.path.join(OUT, "meta.json")))
page = meta["page"]
hv = meta["header_version"]

hdr = bytearray(open(os.path.join(OUT, "header.bin"), "rb").read())
k = open(os.path.join(OUT, "kernel.bin"), "rb").read()
rd = open(os.path.join(OUT, "ramdisk-new.gz"), "rb").read()
dtb = open(os.path.join(OUT, "dtb.bin"), "rb").read()


def au(x, p):
    return ((x + p - 1) // p) * p


struct.pack_into("<I", hdr, 8, len(k))
struct.pack_into("<I", hdr, 16, len(rd))
struct.pack_into("<I", hdr, 24, 0)
if hv >= 2:
    struct.pack_into("<I", hdr, 1648, len(dtb))

buf = bytearray()
buf += hdr
buf += k
buf += b"\x00" * (au(len(buf), page) - len(buf))
buf += rd
buf += b"\x00" * (au(len(buf), page) - len(buf))
if hv >= 2 and dtb:
    buf += dtb
    buf += b"\x00" * (au(len(buf), page) - len(buf))
if len(buf) < meta["orig_total"]:
    buf += b"\x00" * (meta["orig_total"] - len(buf))

open(DST, "wb").write(buf)
print("wrote", DST, len(buf), "bytes (kernel", len(k), "ramdisk", len(rd), "dtb", len(dtb), ")")

v = open(DST, "rb").read()
print("cmdline:", v[64:64+512].split(b"\x00", 1)[0].decode())
print("k_off", page, "rd_off", page + au(len(k), page))
