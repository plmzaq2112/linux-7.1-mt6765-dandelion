#!/bin/sh
# Install the Ubuntu rootfs onto userdata (mmcblk0p41) with guards.
DEV=/dev/mmcblk0p41
MNT=/mnt/ubuntu
E2LD=/opt/e2fs/lib:/opt/e2fs/usr/lib
E2CFG=/opt/e2fs/etc/mke2fs.conf

SZ=$(cat /sys/class/block/mmcblk0p41/size 2>/dev/null || echo 0)
if [ "$SZ" -lt 20971520 ]; then
	echo "ABORT: mmcblk0p41 size ${SZ} sectors is not userdata-sized"
	exit 1
fi

if [ ! -x /opt/e2fs/sbin/mke2fs ]; then
	echo "ABORT: /opt/e2fs/sbin/mke2fs missing"
	exit 1
fi

echo "formatting $DEV (ext4)"
LD_LIBRARY_PATH=$E2LD MKE2FS_CONFIG=$E2CFG /opt/e2fs/sbin/mke2fs -t ext4 -F -L ubuntu "$DEV" || exit 1

mkdir -p "$MNT"
mount "$DEV" "$MNT" || exit 1

echo "receiving rootfs on port 3801 ..."
nc -l -p 3801 < /dev/null | tar -xzf - -C "$MNT"
TRC=$?
echo "tar rc=$TRC"

sync
if [ "$TRC" -ne 0 ]; then
	echo "ABORT: tar failed; p41 left unmounted and unmarked"
	umount "$MNT"
	exit 1
fi

echo "checks:"
for f in sbin/init usr/libexec/phosh etc/fstab etc/systemd/system/focaltech-touch.service lib/modules/focaltech_ts.ko; do
	if [ -e "$MNT/$f" ]; then echo "  OK  $f"; else echo "  MISSING $f"; fi
done
echo "size: $(du -sh "$MNT" 2>/dev/null)"
echo "files: $(find "$MNT" | wc -l)"
umount "$MNT"
echo "INSTALL_DONE (marker NOT created; test boot manually first)"
