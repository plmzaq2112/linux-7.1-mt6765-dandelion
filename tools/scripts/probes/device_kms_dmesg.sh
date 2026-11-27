#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export VK_KMS_SECS=5
systemctl stop greetd
sleep 3
dmesg -C 2>/dev/null
timeout 60 ./vk_kms2 2>&1 | tail -3
sleep 1
echo "=== dmesg (kick/ccb/freelist/fw) ==="
timeout 10 dmesg 2>/dev/null | grep -iE 'kccb|retry|freelist|kick|firmware|fw ' | tail -15
systemctl start greetd
echo DONE
