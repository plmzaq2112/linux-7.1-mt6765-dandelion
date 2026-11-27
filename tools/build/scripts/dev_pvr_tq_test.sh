#!/bin/sh
set -x
systemctl stop greetd
sleep 3
rmmod pvrsrvkm
sleep 1
insmod /root/pvrsrvkm-dump.ko pvr_apm=0 pvr_os_active=1
sleep 1
lsmod | grep pvrsrvkm
ls /sys/module/pvrsrvkm/parameters/ | grep -i dump
ls /dev/dri/
echo 5 > /sys/module/pvrsrvkm/parameters/pvr_dump_tq
echo 5 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
dmesg -C
export LD_LIBRARY_PATH=/root/pvr64:/opt/pvr/lib
/root/pvr_gles2_test 2>&1 | tail -10
sleep 1
dmesg | grep -E "pvr-dump-TQ|pvr-dump:" | head -40
