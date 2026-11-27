#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export VK_COMP_VERIFY=1
export VK_KMS_SECS=2
export VK_COMP_LAYERS=1
export PVR13_DUMP_SCISSOR=1
systemctl stop greetd
sleep 3
echo "== ISP scissor enabled, words as upstream"
PVR13_SCISSOR=1 timeout 60 ./vk_comp > /tmp/sc_a.txt 2>&1
grep -E 'pvr-scissor: rect|verify: slot=0|presented' /tmp/sc_a.txt | head -6
echo "== ISP scissor enabled, 16-bit halves swapped"
PVR13_SCISSOR=1 PVR13_SCISSOR_SWAP=1 timeout 60 ./vk_comp > /tmp/sc_b.txt 2>&1
grep -E 'pvr-scissor: rect|verify: slot=0|presented' /tmp/sc_b.txt | head -6
systemctl start greetd
echo DONE
