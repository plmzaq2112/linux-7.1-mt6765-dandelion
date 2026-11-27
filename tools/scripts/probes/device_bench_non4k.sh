#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=15
systemctl stop greetd
sleep 3
echo "=== 720x1600 default (4K heap) ==="
timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== 720x1600 NON-4K heap ==="
PVR13_NON4K=1 timeout 180 ./vk_geom720 2>&1 | grep -E 'bench|pvr-heap' | tail -2
echo "=== 64x64 NON-4K heap ==="
PVR13_NON4K=1 timeout 120 ./vk_geom64 2>&1 | grep -E 'bench|pvr-heap' | tail -2
systemctl start greetd
echo DONE
