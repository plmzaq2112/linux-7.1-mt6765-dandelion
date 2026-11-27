#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export VK_KMS_SECS=4
export PVR13_TIME=1
systemctl stop greetd
sleep 3
timeout 60 ./vk_kms2 2>&1 | grep -E 'pvr-time|avg:|presented' | tail -14
systemctl start greetd
echo DONE
