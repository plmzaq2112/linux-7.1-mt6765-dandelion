#!/bin/sh
# Full 320B 3D + 80B TA golden for the GLES clear at 64x64 (for field diffing).
systemctl stop greetd 2>/dev/null
sleep 2
rmmod pvrsrvkm 2>/dev/null
sleep 1
insmod /root/pvrsrvkm-dump2.ko pvr_apm=0
sleep 1

export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw

echo 1 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
dmesg -C
/root/gles_clear 64 64 1 0 0 2>&1 | tail -1
sleep 1
echo "=== TA full ==="
dmesg | grep "pvr-dump-TA: 0000" | head -6
echo "=== 3D full ==="
dmesg | grep "pvr-dump-3D: 0000" | head -21

rmmod pvrsrvkm
sleep 1
insmod /root/pvrsrvkm.ko.orig pvr_apm=0
sleep 1
systemctl start greetd
