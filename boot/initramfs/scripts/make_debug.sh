#!/bin/bash
# Build a debug boot image: initramfs no longer recognizes the boot marker,
# so it always falls back to the serial shell.
set -e

W="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"/rootfs/ubuntu/boot
rm -rf /tmp/db
mkdir -p /tmp/db

python3 "$W/unpack_rd.py"

cd /tmp/db
mkdir rd
cd rd
gzip -dc ../ramdisk.gz | cpio -idm --quiet
echo "--- marker refs in init ---"
grep -n "dandelion-rootfs-ok" init || true
sed -i 's/dandelion-rootfs-ok/dandelion-DEBUG-ok/g' init
grep -n "dandelion-DEBUG-ok" init
ls -l init

find . -print0 | cpio --null -o -H newc --owner 0:0 --quiet | gzip -9 > ../ramdisk-new.gz
ls -l ../ramdisk-new.gz
cd /tmp/db
python3 "$W/repack_boot.py"
md5sum "$W/boot-debug.img"
