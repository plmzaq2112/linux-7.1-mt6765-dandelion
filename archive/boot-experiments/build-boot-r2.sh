#!/bin/bash
# Build test image #2: same 7.1 kernel, but:
#   - DTB = r96 (has all 52 dtbo overlay symbols; LK's fdt_bootargs assert needs it)
#   - init = never-exit init with USB CDC-ACM console
#   - cmdline = base + ramoops params (so a panic lands in TWRP-readable pstore)
set -e

R="$HOME/AI Project/Redmi 9A/kernel 7.1 mainline"
W="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"
cd "$R"

cp "$W/scripts/init-busybox-7.1.sh" initramfs-busybox/init
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
print("r96 dtb: %d bytes, __symbols__=%s" % (len(dtb), b"__symbols__" in dtb))
PY

# refreshed gzip image (Image was rebuilt only for DTBs; Image is unchanged)
gzip -9 -c out/arch/arm64/boot/Image > out/arch/arm64/boot/Image.gz

# NOTE: boot header cmdline is 512 bytes total (NUL included) - keep it short.
CMDLINE="bootopt=64S3,32N2,64N2 kpti=off ignore_loglevel log_buf_len=4M fbcon=font:TER16x32 console=tty0 console=ttyGS0 panic=0 ramoops.mem_address=0x47c90000 ramoops.mem_size=0xe0000 ramoops.console_size=0x40000 ramoops.pmsg_size=0x10000"

python3 "$W/mt6765-mainline-m2/pack_boot_mainline.py" \
	"$W/mt6765-mainline-m3/boot-7.1-dandelion-r96-android64-log.img" \
	boot-7.1-dandelion-busybox-r2.img \
	out/arch/arm64/boot/Image.gz \
	initramfs-busybox.cpio.gz \
	r96-dandelion.dtb \
	"$CMDLINE"

sha256sum boot-7.1-dandelion-busybox-r2.img
cp boot-7.1-dandelion-busybox-r2.img "$W/dist/images/boot-7.1-dandelion-busybox-r2.img"
echo "copied to dist/images/"
