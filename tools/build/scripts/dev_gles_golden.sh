#!/bin/sh
systemctl stop greetd
sleep 2
rmmod pvrsrvkm
sleep 1
insmod /root/pvrsrvkm-dump2.ko pvr_apm=0
sleep 1
echo 4 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
dmesg -C

export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw
/root/gles_clear 64 64 1 0 0 2>&1 | tail -2
sleep 1
echo "--- dmesg ---"
dmesg | grep -E "pvr-dump:" | head -4
dmesg | grep -A24 "pvr-dump-3D" | head -25
dmesg | grep -A6 "pvr-dump-TA" | head -7

systemctl start greetd
