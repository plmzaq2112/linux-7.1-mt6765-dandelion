#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
systemctl stop greetd
sleep 3
echo "== autodrag self-test (no physical touch needed)"
VK_COMP_AUTODRAG=1 VK_COMP_LAYERS=4 VK_KMS_SECS=2 timeout 60 ./vk_comp > /tmp/ad.txt 2>&1
grep -E 'input:|touch:|autodrag|presented' /tmp/ad.txt
echo "== verify still renders after the simulated drag"
VK_COMP_AUTODRAG=1 VK_COMP_LAYERS=4 VK_KMS_SECS=2 VK_COMP_VERIFY=1 timeout 60 ./vk_comp > /tmp/ad2.txt 2>&1
grep -E 'verify: slot=0' /tmp/ad2.txt
systemctl start greetd
echo DONE
