#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=2
systemctl stop greetd
sleep 3
echo "=== log2=14 stderr ==="
PVR13_PAGE_LOG2=14 timeout 60 ./vk_geom720 2>&1 | head -12
echo "=== log2=14 kernel log ==="
timeout 10 dmesg | tail -6
systemctl start greetd
echo DONE
