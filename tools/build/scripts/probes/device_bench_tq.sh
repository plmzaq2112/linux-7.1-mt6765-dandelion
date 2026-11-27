#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_TQ_LOOP=15
systemctl stop greetd
sleep 3
echo "=== TQ clear 64x64 ==="
timeout 120 ./vk_clear_tq64 2>/dev/null | grep -E 'tq bench'
echo "=== TQ clear 720x1600 ==="
timeout 180 ./vk_clear_tq720 2>/dev/null | grep -E 'tq bench'
systemctl start greetd
echo DONE
