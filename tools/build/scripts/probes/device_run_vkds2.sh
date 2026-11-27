#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
systemctl stop greetd
sleep 3
echo "=== D16 depth ==="
timeout 60 ./vk_ds 2>/dev/null | tail -4
echo "=== D32_SFLOAT depth ==="
VK_DS_D32=1 timeout 60 ./vk_ds 2>/dev/null | tail -4
systemctl start greetd
echo DONE
