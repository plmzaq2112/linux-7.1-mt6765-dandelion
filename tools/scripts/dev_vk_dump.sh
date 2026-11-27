#!/bin/sh
cp -f /tmp/pvr-vk/libvulkan_powervr_mesa.so /tmp/pvr-vk/libvulkan_powervr_mesa.so.bak 2>/dev/null
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export PVR_DUMP_CMD=1
cd /tmp/pvr-vk
./vk_clear_test 2>&1 | tail -80
