#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export PVR_DEBUG=cs
systemctl stop greetd
sleep 3
VK_COMP_LAYERS=1 VK_KMS_SECS=2 timeout 60 ./vk_comp > /tmp/comp_cs.txt 2>&1
grep -E 'pres_region_clip|pres_ispctl_dbsc|scenable|scindex|dbindex|left|right|top|bottom|STATE_ISP|STATE_PPP_CTRL|ISPCTL' /tmp/comp_cs.txt | head -24
systemctl start greetd
echo DONE
