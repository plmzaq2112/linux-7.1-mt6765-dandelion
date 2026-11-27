#!/bin/sh
systemctl stop greetd
sleep 2
rmmod pvrsrvkm
sleep 1
insmod /root/pvrsrvkm-dump2.ko pvr_apm=0
echo "insmod rc=$?"
sleep 1
lsmod | grep pvrsrvkm
echo 6 > /sys/module/pvrsrvkm/parameters/pvr_dump_tq
echo 3 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
dmesg -C
systemctl start greetd
sleep 10
echo "--- dmesg ---"
dmesg | grep -E "pvr-dump-TQ: prepare|pvr-dump: Kick|pvr-dump-TQ: [0-9a-f]{4}" | head -30
