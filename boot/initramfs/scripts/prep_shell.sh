#!/bin/bash
set -e
W="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"/rootfs/ubuntu/boot
rm -rf /tmp/sb
mkdir -p /tmp/sb
cd /tmp/sb
python3 - <<'PY'
import struct, os
src = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-console2.img"
d = open(src, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0] if hv >= 2 else 0
au = lambda x, p: ((x + p - 1) // p) * p
k_off = page
rd_off = k_off + au(ks, page)
dtb_off = rd_off + au(rs, page)
os.makedirs("/tmp/sb", exist_ok=True)
open("/tmp/sb/header.bin", "wb").write(d[:page])
open("/tmp/sb/kernel.bin", "wb").write(d[k_off:k_off+ks])
open("/tmp/sb/ramdisk.gz", "wb").write(d[rd_off:rd_off+rs])
open("/tmp/sb/dtb.bin", "wb").write(d[dtb_off:dtb_off+ds])
open("/tmp/sb/meta.txt", "w").write("%d %d %d %d %d %d\n" % (page, hv, ks, rs, ds, len(d)))
print("page", page, "ks", ks, "rs", rs, "ds", ds, "total", len(d))
PY
mkdir rd
cd rd
gzip -dc ../ramdisk.gz | cpio -idm --quiet
echo "==== init tail ===="
tail -30 init
