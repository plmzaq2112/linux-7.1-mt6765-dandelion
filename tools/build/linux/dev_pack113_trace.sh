#!/bin/sh
# Same as dev_pack113_run.sh but enables the firmware trace buffer and page
# fault debug so the watchdog dump explains the lockup.
systemctl stop greetd 2>/dev/null
sleep 2
rmmod pvrsrvkm 2>/dev/null
sleep 1
insmod /root/pvrsrvkm-dump2.ko pvr_apm=0 FWTraceBufSizeInDWords=8192 EnablePageFaultDebug=1
sleep 1

echo 0 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
dmesg -C

cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
timeout 15 ./vk_clear2 > clear2.log 2>&1
echo "vk rc=$?"
sleep 3

dmesg > /tmp/dmesg-trace.log
echo "=== summary ==="
grep -E "Number of HWR|Recovery|FW Trace|FW thread|Page fault|page fault|EventStatus|Guilty" /tmp/dmesg-trace.log | tail -30
echo "=== result ==="
grep -E "words=|first32" clear2.log | head -3
