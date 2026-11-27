#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=10
systemctl stop greetd
sleep 3
echo "=== full surface (region clip default) ==="
timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== region clip 2x2 tiles (32x32) ==="
PVR13_RGN_R=2 PVR13_RGN_B=2 timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== region clip 10x10 tiles (160x160) ==="
PVR13_RGN_R=10 PVR13_RGN_B=10 timeout 180 ./vk_geom720 2>/dev/null | grep bench
systemctl start greetd
echo DONE
