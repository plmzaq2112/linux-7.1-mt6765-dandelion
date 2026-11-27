#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=2
export PVR13_HEAPS=1
systemctl stop greetd
sleep 3
timeout 60 ./vk_geom720 2>&1 | grep -E 'pvr-heap|bench' | head -12
systemctl start greetd
echo DONE
