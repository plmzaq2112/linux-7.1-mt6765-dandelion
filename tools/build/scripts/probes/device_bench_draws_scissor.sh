#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=10
systemctl stop greetd
sleep 3
echo "=== 64 draws, full-screen scissor ==="
VK_GEOM_DRAWS=64 timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== 64 draws, scissor 64x64 ==="
VK_GEOM_DRAWS=64 SX=0 SY=0 SW=64 SH=64 timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== 64 draws, scissor 256x256 ==="
VK_GEOM_DRAWS=64 SX=0 SY=0 SW=256 SH=256 timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== 1 draw, full-screen (reference) ==="
VK_GEOM_DRAWS=1 timeout 180 ./vk_geom720 2>/dev/null | grep bench
systemctl start greetd
echo DONE
