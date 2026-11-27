#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=10
systemctl stop greetd
sleep 3
echo "=== full 720x1600 ==="
timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== scissor 32x32 ==="
SX=0 SY=0 SW=32 SH=32 timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== scissor 256x256 ==="
SX=0 SY=0 SW=256 SH=256 timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== scissor 64x1600 (thin strip) ==="
SX=0 SY=0 SW=64 SH=1600 timeout 180 ./vk_geom720 2>/dev/null | grep bench
systemctl start greetd
echo DONE
