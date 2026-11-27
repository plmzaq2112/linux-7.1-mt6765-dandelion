#!/bin/sh
# Lockup diagnosis with the full-debug KM (pvrsrvkm.ko.orig).
systemctl stop greetd 2>/dev/null
sleep 2
rmmod pvrsrvkm 2>/dev/null
sleep 1
insmod /root/pvrsrvkm.ko.orig pvr_apm=0 FWTraceBufSizeInDWords=8192 EnablePageFaultDebug=1
sleep 1
dmesg -C

cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
timeout 15 ./vk_clear2 > clear2.log 2>&1
echo "vk rc=$?"
sleep 3

dmesg > /tmp/dmesg-orig.log
echo "=== key lines ==="
grep -E "RGX Info|Number of HWR|Recovery|FW Trace|FW thread|Page fault|page fault|EventStatus|Guilty|HWRState|FW State|CCB" /tmp/dmesg-orig.log | tail -40
echo "=== result ==="
grep -E "words=|first32" clear2.log | head -3
