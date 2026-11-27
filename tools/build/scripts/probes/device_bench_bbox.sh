#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export VK_COMP_VERIFY=1
export VK_KMS_SECS=2
export VK_COMP_LAYERS=1
export PVR13_NOSCISSOR=1
systemctl stop greetd
sleep 3
echo "== region clip with -1 (default) =="
timeout 60 ./vk_comp > /tmp/bb_old.txt 2>&1
grep -E 'rect=|slot=0' /tmp/bb_old.txt
echo "== region clip exclusive (no -1) =="
PVR13_RGN_EXCL=1 timeout 60 ./vk_comp > /tmp/bb_new.txt 2>&1
grep -E 'rect=|slot=0' /tmp/bb_new.txt
systemctl start greetd
echo DONE
