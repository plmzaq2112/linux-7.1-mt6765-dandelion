#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export VK_COMP_VERIFY=1
export VK_KMS_SECS=2
export VK_COMP_LAYERS=1
systemctl stop greetd
sleep 3
echo "=== zero-copy (import) ==="
timeout 60 ./vk_comp > /tmp/comp_zc.txt 2>&1
grep -E 'verify: slot|vbo' /tmp/comp_zc.txt
echo "=== fallback (PVR image + CPU copy) ==="
VK_KMS_DUMB=1 timeout 60 ./vk_comp > /tmp/comp_fb.txt 2>&1
grep -E 'verify: slot|vbo' /tmp/comp_fb.txt
systemctl start greetd
echo DONE
