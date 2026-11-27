#!/usr/bin/env python3
"""Extract ramdisk from the r2 boot image and inspect /init."""
import gzip
import io
import struct

img = ("/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
       "dist/images/boot-7.1-dandelion-busybox-r2.img")
d = open(img, "rb").read()
print("image size:", len(d), "magic:", d[:8])
page = struct.unpack_from("<I", d, 36)[0]
ksz = struct.unpack_from("<I", d, 8)[0]
rsz = struct.unpack_from("<I", d, 16)[0]
off = (page + ksz + page - 1) // page * page
rd = d[off:off + rsz]
print("page=%d ksz=%d rsz=%d ramdisk_off=%d" % (page, ksz, rsz, off))

data = gzip.decompress(rd)
print("cpio size:", len(data))

# minimal newc parser
pos = 0
files = {}
while pos + 110 <= len(data):
    if data[pos:pos + 6] != b"070701":
        break
    fields = [int(data[pos + 6 + i * 8:pos + 6 + (i + 1) * 8], 16) for i in range(13)]
    mode, filesize, namesize = fields[1], fields[6], fields[11]
    name = data[pos + 110:pos + 110 + namesize - 1].decode("latin1")
    pos = (pos + 110 + namesize + 3) & ~3
    body = data[pos:pos + filesize]
    pos = (pos + filesize + 3) & ~3
    files[name] = (mode, body)
    if name == "TRAILER!!!":
        break

print("entries:", len(files))
init = files.get("init")
if init:
    mode, body = init
    print("init mode=%o size=%d" % (mode, len(body)))
    text = body.decode("latin1", "replace")
    for ln in text.splitlines():
        if any(k in ln for k in ("idVendor", "idProduct", "G=", "UDC", "ttyGS", "g1", "0525", "1d6b")):
            print("  |", ln)
else:
    print("no /init found; entries sample:", list(files)[:30])
