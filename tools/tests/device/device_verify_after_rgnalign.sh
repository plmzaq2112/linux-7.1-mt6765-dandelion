#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
systemctl stop greetd
sleep 3
echo "=== vk_kms2 zero-copy 720x1600 ==="
VK_KMS_DRM=/dev/dri/card1 VK_KMS_SECS=8 timeout 90 ./vk_kms2 2>&1 | tail -4
echo "=== colored quad (varying) ==="
timeout 60 ./vk_colored_quad 2>&1 | grep -E 'words='
echo "=== textured quad ==="
timeout 60 ./vk_textured_quad 2>&1 | grep -E 'words='
echo "=== render-pass clear ==="
timeout 60 ./vk_clear2 2>&1 | grep -E 'words='
systemctl start greetd
echo DONE
