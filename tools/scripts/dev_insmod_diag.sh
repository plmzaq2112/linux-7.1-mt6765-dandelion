#!/bin/sh
systemctl stop greetd
sleep 2
rmmod pvrsrvkm
sleep 1
dmesg -C
insmod /root/pvrsrvkm-dump.ko pvr_apm=0
echo "insmod rc=$?"
dmesg | tail -8
insmod /root/pvrsrvkm.ko.orig pvr_apm=0
echo "restore rc=$?"
systemctl start greetd
