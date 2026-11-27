#!/bin/sh
systemctl stop greetd 2>/dev/null
sleep 2
export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw

echo 1 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
dmesg -C
/root/gles_clear 32 32 0 1 0 2>&1 | tail -1
sleep 1
echo "=== 32x32 green 3D ==="
dmesg | grep -A20 "pvr-dump-3D" | head -21
echo "=== 32x32 green TA ==="
dmesg | grep -A5 "pvr-dump-TA" | head -6

echo 1 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
dmesg -C
/root/gles_clear 128 128 0 0 1 2>&1 | tail -1
sleep 1
echo "=== 128x128 blue 3D ==="
dmesg | grep -A20 "pvr-dump-3D" | head -21
echo "=== 128x128 blue TA ==="
dmesg | grep -A5 "pvr-dump-TA" | head -6

systemctl start greetd
