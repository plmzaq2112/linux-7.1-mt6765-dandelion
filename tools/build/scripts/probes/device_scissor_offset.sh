#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
systemctl stop greetd
sleep 3
echo "== static scissor 0,0 32x32"
SX=0 SY=0 SW=32 SH=32 timeout 60 ./vk_geom64 2>/dev/null | grep -E 'green='
echo "== static scissor 32,32 32x32"
SX=32 SY=32 SW=32 SH=32 timeout 60 ./vk_geom64 2>/dev/null | grep -E 'green='
echo "== dyn scissor 0,0 32x32"
VK_GEOM_DYNSC=1 SX=0 SY=0 SW=32 SH=32 timeout 60 ./vk_geom64 2>/dev/null | grep -E 'green='
echo "== dyn scissor 32,32 32x32"
VK_GEOM_DYNSC=1 SX=32 SY=32 SW=32 SH=32 timeout 60 ./vk_geom64 2>/dev/null | grep -E 'green='
systemctl start greetd
echo DONE
