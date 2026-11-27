#!/bin/sh
# Run Mesa vk_clear2 against the dump-enabled KM and capture the exact
# 1.13 payloads produced by the new packer.
systemctl stop greetd 2>/dev/null
sleep 2
rmmod pvrsrvkm 2>/dev/null
sleep 1
insmod /root/pvrsrvkm-dump2.ko pvr_apm=0
sleep 1

echo 4 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
dmesg -C

cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export PVR_DUMP_CMD=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
timeout 15 ./vk_clear2 > clear2.log 2>&1
echo "vk rc=$?"
sleep 1

echo "=== kicks ==="
dmesg | grep "pvr-dump: Kick" | head -6
echo "=== TA 113 ==="
dmesg | grep "pvr-dump-TA:" | head -6
echo "=== 3D 113 ==="
dmesg | grep "pvr-dump-3D:" | head -21
echo "=== result ==="
grep -E "words=|first32|failed" clear2.log | head -5
