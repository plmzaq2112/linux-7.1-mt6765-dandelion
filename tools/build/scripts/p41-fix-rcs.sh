#!/bin/sh
# quick patch script run on the device (via adb shell) while p41 is mounted
P=/mnt/p41

# 1) rcS: guard every potentially-blocking step with timeout
if [ -f $P/etc/init.d/rcS ]; then
    sed -i 's|^\[ -f /root/focaltech_ts.ko \] && insmod /root/focaltech_ts.ko 2>/dev/null|timeout 10 insmod /root/focaltech_ts.ko 2>/dev/null|' $P/etc/init.d/rcS
    grep -n "focaltech_ts" $P/etc/init.d/rcS
fi

# 2) restore marker so initramfs switches root
touch $P/etc/dandelion-rootfs-ok
ls -l $P/etc/dandelion-rootfs-ok
