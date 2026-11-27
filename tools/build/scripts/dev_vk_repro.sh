#!/bin/sh
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
dmesg -C 2>/dev/null
cd /tmp/pvr-vk
./vk_probe 2>&1 | head -12
echo "---- clear test ----"
./vk_clear_test 2>&1 | head -20
echo "---- dmesg ----"
dmesg | tail -20
