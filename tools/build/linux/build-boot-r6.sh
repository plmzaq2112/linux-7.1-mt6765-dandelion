#!/bin/bash
# Build test image #5: quiet ttyGS0 until the host sends a byte.
set -e

R="$HOME/AI Project/Redmi 9A/kernel 7.1 mainline"
W="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"
cd "$R"

cp "$W/scripts/init-busybox-r6.sh" initramfs-busybox/init
chmod +x initramfs-busybox/init

(cd initramfs-busybox && find . -print0 | cpio --null -o --format=newc 2>/dev/null | gzip -9 > ../initramfs-busybox.cpio.gz)

python3 - <<'PY'
import struct
p = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/mt6765-mainline-m3/boot-7.1-dandelion-r96-android64-log.img"
d = open(p, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ksz = struct.unpack_from("<I", d, 8)[0]
rsz = struct.unpack_from("<I", d, 16)[0]
ssz = struct.unpack_from("<I", d, 24)[0]
rdsz = struct.unpack_from("<I", d, 1632)[0] if hv >= 2 else 0
dsz = struct.unpack_from("<I", d, 1648)[0] if hv >= 2 else 0
off = page
for x in (ksz, rsz, ssz, rdsz):
    off = (off + x + page - 1) // page * page
dtb = d[off:off + dsz]
assert dtb[:4] == b"\xd0\x0d\xfe\xed", dtb[:4]
open("/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/r96-dandelion.dtb", "wb").write(dtb)
PY

python3 "$W/scripts/patch-dtb-console.py" \
	"$R/r96-dandelion.dtb" \
	"$R/r96-dandelion-noconsole.dtb" >/dev/null

gzip -9 -c out/arch/arm64/boot/Image > out/arch/arm64/boot/Image.gz

CMDLINE="bootopt=64S3,32N2,64N2 kpti=off ignore_loglevel log_buf_len=4M fbcon=font:TER16x32 console=tty0 panic=0 ramoops.mem_address=0x47c90000 ramoops.mem_size=0xe0000 ramoops.console_size=0x40000 ramoops.pmsg_size=0x10000"

python3 "$W/mt6765-mainline-m2/pack_boot_mainline.py" \
	"$W/mt6765-mainline-m3/boot-7.1-dandelion-r96-android64-log.img" \
	boot-7.1-dandelion-busybox-r6.img \
	out/arch/arm64/boot/Image.gz \
	initramfs-busybox.cpio.gz \
	r96-dandelion-noconsole.dtb \
	"$CMDLINE"

sha256sum boot-7.1-dandelion-busybox-r6.img
cp boot-7.1-dandelion-busybox-r6.img "$W/dist/images/boot-7.1-dandelion-busybox-r6.img"
echo "copied to dist/images/"
