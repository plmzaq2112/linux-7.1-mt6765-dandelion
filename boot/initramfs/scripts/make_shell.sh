#!/bin/bash
# Build a boot image whose initramfs switches root into p41 but runs /bin/sh
# instead of systemd, giving a root shell on the serial console.
set -e
W="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"/rootfs/ubuntu/boot
SRC="$W"/boot-console2.img

rm -rf /tmp/sb
mkdir -p /tmp/sb/rd
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
open("/tmp/sb/header.bin", "wb").write(d[:page])
open("/tmp/sb/kernel.bin", "wb").write(d[k_off:k_off+ks])
open("/tmp/sb/ramdisk.gz", "wb").write(d[rd_off:rd_off+rs])
open("/tmp/sb/dtb.bin", "wb").write(d[dtb_off:dtb_off+ds])
open("/tmp/sb/meta.txt", "w").write("%d %d %d %d %d %d\n" % (page, hv, ks, rs, ds, len(d)))
print("unpacked: page", page, "ks", ks, "rs", rs, "ds", ds)
PY

cd /tmp/sb/rd
gzip -dc ../ramdisk.gz | cpio -idm --quiet

sed -i 's|exec switch_root /newroot /sbin/init|exec switch_root /newroot /bin/sh -i|' init
grep -n 'exec switch_root' init

find . -print0 | cpio --null -o -H newc --owner 0:0 --quiet | gzip -9 > /tmp/sb/ramdisk-new.gz
ls -l /tmp/sb/ramdisk-new.gz

cd /tmp/sb
python3 - <<'PY'
import struct
page, hv, ks, rs, ds, total = map(int, open("/tmp/sb/meta.txt").read().split())
hdr = bytearray(open("/tmp/sb/header.bin", "rb").read())
k = open("/tmp/sb/kernel.bin", "rb").read()
rd = open("/tmp/sb/ramdisk-new.gz", "rb").read()
dtb = open("/tmp/sb/dtb.bin", "rb").read()
au = lambda x, p: ((x + p - 1) // p) * p
struct.pack_into("<I", hdr, 8, len(k))
struct.pack_into("<I", hdr, 16, len(rd))
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
if len(buf) < total:
    buf += b"\x00" * (total - len(buf))
out = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-shell.img"
open(out, "wb").write(buf)
print("wrote", out, len(buf))
PY
md5sum "$W/boot-shell.img"
