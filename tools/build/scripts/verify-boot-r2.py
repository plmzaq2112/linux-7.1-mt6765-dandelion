#!/usr/bin/env python3
import gzip
import struct

p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/boot-7.1-dandelion-busybox-r2.img"
d = open(p, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
ksz = struct.unpack_from("<I", d, 8)[0]
rsz = struct.unpack_from("<I", d, 16)[0]
dsz = struct.unpack_from("<I", d, 1648)[0]
cmd = d[64:64 + 512].split(b"\x00", 1)[0].decode()
print("image size:", len(d))
print("cmdline(%d): %s" % (len(cmd), cmd))
off = page + ((ksz + page - 1) // page) * page
rd = d[off:off + rsz]
dtb = d[off + ((rsz + page - 1) // page) * page:][:dsz]
print("kernel:", ksz, "ramdisk:", rsz, "dtb:", dsz,
      "dtb_magic:", dtb[:4].hex(), "dtb_has_symbols:", b"__symbols__" in dtb)
raw = gzip.decompress(rd)
print("initramfs has new init:", b"dandelion busybox initramfs ready" in raw,
      "| has ttyGS0 setup:", b"ttyGS0" in raw,
      "| has respawn loop:", b"respawning in 1s" in raw)
