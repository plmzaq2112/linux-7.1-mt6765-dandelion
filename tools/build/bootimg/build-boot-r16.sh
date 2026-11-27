#!/bin/bash
# Build test image #13:
#   - panel reset polarity fixed (assert low, release after bias)
#   - DTB r96-pwmbl.dtb: same as r96-noconsole + mt6370 backlight node
set -e

R="$HOME/AI Project/Redmi 9A/kernel 7.1 mainline"
W="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"
cd "$R"

cp "$W/scripts/init-busybox-r11.sh" initramfs-busybox/init
chmod +x initramfs-busybox/init

(cd initramfs-busybox && find . -print0 | cpio --null -o --format=newc 2>/dev/null | gzip -9 > ../initramfs-busybox.cpio.gz)

gzip -9 -c out/arch/arm64/boot/Image > out/arch/arm64/boot/Image.gz

CMDLINE="bootopt=64S3,32N2,64N2 kpti=off ignore_loglevel log_buf_len=4M fbcon=font:TER16x32 console=tty0 panic=0 ramoops.mem_address=0x47c90000 ramoops.mem_size=0xe0000 ramoops.console_size=0x40000 ramoops.pmsg_size=0x10000"

python3 "$W/mt6765-mainline-m2/pack_boot_mainline.py" \
	"$W/mt6765-mainline-m3/boot-7.1-dandelion-r96-android64-log.img" \
	boot-7.1-dandelion-busybox-r16.img \
	out/arch/arm64/boot/Image.gz \
	initramfs-busybox.cpio.gz \
	"$HOME/r96-pwmbl.dtb" \
	"$CMDLINE"

sha256sum boot-7.1-dandelion-busybox-r16.img
cp boot-7.1-dandelion-busybox-r16.img "$W/dist/images/boot-7.1-dandelion-busybox-r16.img"
echo "copied to dist/images/"


