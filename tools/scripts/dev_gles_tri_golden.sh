#!/bin/sh
# Capture the 1.13 TA/3D golden for a GLES draw (triangle) using the vendor UM.
systemctl stop greetd 2>/dev/null
sleep 2
rmmod pvrsrvkm 2>/dev/null
sleep 1
insmod /root/pvrsrvkm-dump2.ko pvr_apm=0
sleep 1

export LD_LIBRARY_PATH=/root/pvr64:/root/pvr64/egl:/root/pvr64/hw

echo 1 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
dmesg -C
/root/pvr_gles2_test 2>&1 | tail -3
sleep 1
echo "=== kicks ==="
dmesg | grep "pvr-dump: KickTA3D"
echo "=== TA ==="
dmesg | grep -A6 "pvr-dump-TA" | head -7
echo "=== 3D (draw) ==="
dmesg | grep -A24 "pvr-dump-3D" | head -25

rmmod pvrsrvkm
sleep 1
insmod /root/pvrsrvkm.ko.orig pvr_apm=0
sleep 1
systemctl start greetd
