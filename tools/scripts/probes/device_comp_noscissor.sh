#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export VK_COMP_VERIFY=1
export VK_KMS_SECS=2
systemctl stop greetd
sleep 3
for n in 1 4; do
  echo "== layers=$n, ISP scissor disabled =="
  VK_COMP_LAYERS=$n PVR13_NOSCISSOR=1 timeout 60 ./vk_comp > /tmp/comp_ns$n.txt 2>&1
  grep -E 'verify: slot=0|presented' /tmp/comp_ns$n.txt
done
systemctl start greetd
echo DONE
