import os

D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")

marker = os.path.join(R, "etc/dandelion-rootfs-ok")
if os.path.exists(marker):
    os.remove(marker)
    print("removed rootfs marker (must be created manually after a successful test boot)")
else:
    print("marker not present")

# device-side installer script (copy to device later)
dev = """#!/bin/sh
# Install the Ubuntu rootfs onto userdata (mmcblk0p41) with guards.
DEV=/dev/mmcblk0p41
MNT=/mnt/ubuntu

SZ=$(cat /sys/class/block/mmcblk0p41/size 2>/dev/null || echo 0)
if [ "$SZ" -lt 20971520 ]; then
	echo "ABORT: mmcblk0p41 size ${SZ} sectors is not userdata-sized"
	exit 1
fi

echo "formatting $DEV (ext4)"
mkfs.ext4 -F -L ubuntu "$DEV" || exit 1

mkdir -p "$MNT"
mount "$DEV" "$MNT" || exit 1

echo "receiving rootfs on port 3801 ..."
nc -l -p 3801 | tar -xzf - -C "$MNT"
TRC=$?
echo "tar rc=$TRC"

sync
if [ "$TRC" -ne 0 ]; then
	echo "ABORT: tar failed; leaving p41 unmounted and unmarked"
	umount "$MNT"
	exit 1
fi

echo "checks:"
for f in sbin/init usr/bin/phosh etc/fstab etc/systemd/system/focaltech-touch.service lib/modules/focaltech_ts.ko; do
	if [ -e "$MNT/$f" ]; then echo "  OK  $f"; else echo "  MISSING $f"; fi
done
echo "size: $(du -sh "$MNT" 2>/dev/null)"
echo "files: $(find "$MNT" | wc -l)"
umount "$MNT"
echo "INSTALL_DONE (marker NOT created; test boot manually first)"
"""
open(os.path.join(D, "install-p41.sh"), "w").write(dev)
os.chmod(os.path.join(D, "install-p41.sh"), 0o755)
print("install-p41.sh written")
