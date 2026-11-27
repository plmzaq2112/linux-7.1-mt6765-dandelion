#!/bin/bash
set -e
R="$HOME/AI Project/Redmi 9A/kernel 7.1 mainline"
W="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"
cd "$R"

CMDLINE="bootopt=64S3,32N2,64N2 kpti=off ignore_loglevel log_buf_len=4M fbcon=font:TER16x32 console=tty0 panic=0 ramoops.mem_address=0x47c90000 ramoops.mem_size=0xe0000 ramoops.console_size=0x40000 ramoops.pmsg_size=0x10000"

python3 "$W/mt6765-mainline-m2/pack_boot_mainline.py" \
	"$W/mt6765-mainline-m3/boot-7.1-dandelion-r96-android64-log.img" \
	boot-7.1-dandelion-busybox-r22.img \
	out/arch/arm64/boot/Image.gz \
	initramfs-busybox.cpio.gz \
	"$HOME/r96-gpu.dtb" \
	"$CMDLINE"

sha256sum boot-7.1-dandelion-busybox-r22.img
cp boot-7.1-dandelion-busybox-r22.img "$W/dist/images/"
echo "done"
