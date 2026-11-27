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
echo "== ISP scissor DISABLED (quirk, reference)"
timeout 60 ./vk_comp > /tmp/sc0.txt 2>&1
grep -E 'verify: slot=0' /tmp/sc0.txt
echo "== ISP scissor ENABLED (upstream words)"
PVR13_SCISSOR=1 timeout 60 ./vk_comp > /tmp/sc1.txt 2>&1
grep -E 'verify: slot=0' /tmp/sc1.txt
echo "== ISP scissor ENABLED + halves swapped"
PVR13_SCISSOR=1 PVR13_SCISSOR_SWAP=1 timeout 60 ./vk_comp > /tmp/sc2.txt 2>&1
grep -E 'verify: slot=0' /tmp/sc2.txt
systemctl start greetd
echo DONE
