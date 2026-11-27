#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
systemctl stop greetd
sleep 3
echo "== input devices"
grep -E '^N:|^H: Handlers' /proc/bus/input/devices | head -12
echo "== compositor with touch input (20 s, touch the screen to drag)"
VK_COMP_LAYERS=8 VK_KMS_SECS=20 timeout 60 ./vk_comp > /tmp/comp_in.txt 2>&1
grep -E 'input:|touch:|layers=|presented' /tmp/comp_in.txt
systemctl start greetd
echo DONE
