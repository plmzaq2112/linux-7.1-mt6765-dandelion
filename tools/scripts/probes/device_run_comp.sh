#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
systemctl stop greetd
sleep 3
echo "=== 8 layers ==="
VK_COMP_LAYERS=8 VK_KMS_SECS=8 timeout 90 ./vk_comp 2>&1 | tail -5
echo "=== 16 layers ==="
VK_COMP_LAYERS=16 VK_KMS_SECS=8 timeout 90 ./vk_comp 2>&1 | tail -5
systemctl start greetd
echo DONE
