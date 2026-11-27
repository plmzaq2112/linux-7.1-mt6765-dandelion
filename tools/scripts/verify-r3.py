#!/usr/bin/env python3
"""Verify r3 image: header cmdline, ramdisk init, DTB symbols."""
import gzip
import struct

p = ("/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
     "dist/images/boot-7.1-dandelion-busybox-r3.img")
d = open(p, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
ksz = struct.unpack_from("<I", d, 8)[0]
rsz = struct.unpack_from("<I", d, 16)[0]
cmd = d[64:64 + 512].split(b"\x00")[0].decode("latin1")
print("header cmdline (%d bytes):" % len(cmd))
print(" ", cmd)
print("  ramoops args:", cmd.count("ramoops."))
print("  console ttyGS0:", "console=ttyGS0" in cmd)

off = (page + ksz + page - 1) // page * page
rd = gzip.decompress(d[off:off + rsz])
pos, init = 0, None
while pos + 110 <= len(rd) and rd[pos:pos + 6] == b"070701":
    f = [int(rd[pos + 6 + i * 8:pos + 6 + (i + 1) * 8], 16) for i in range(13)]
    namesize, filesize = f[11], f[6]
    name = rd[pos + 110:pos + 110 + namesize - 1].decode("latin1")
    pos = (pos + 110 + namesize + 3) & ~3
    body = rd[pos:pos + filesize]
    pos = (pos + filesize + 3) & ~3
    if name == "init":
        init = body
    if name == "TRAILER!!!":
        break
t = init.decode("latin1", "replace")
print("init: %d bytes, idVendor=%s, wait-loop=%s, r3=%s"
      % (len(init), "0x1d6b" in t, "while [ \"$i\" -lt 60 ]" in t, "(r3)" in t))

dtb_off = (off + rsz + page - 1) // page * page
dsz = struct.unpack_from("<I", d, 1648)[0]
dtb = d[dtb_off:dtb_off + dsz]
print("dtb: off=%d size=%d magic=%s symbols=%s"
      % (dtb_off, len(dtb), dtb[:4].hex(), b"__symbols__" in dtb))
print("image size:", len(d))
