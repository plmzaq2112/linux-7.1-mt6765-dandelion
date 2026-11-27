#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
systemctl stop greetd
sleep 3
echo "== scissor 20x20 at 0,0: ISP scissor enabled (exact clip expected)"
SX=0 SY=0 SW=20 SH=20 timeout 60 ./vk_geom64 2>/dev/null | grep words=
echo "== scissor 20x20 at 0,0: ISP scissor disabled (region clip 32px)"
PVR13_NOSCISSOR=1 SX=0 SY=0 SW=20 SH=20 timeout 60 ./vk_geom64 2>/dev/null | grep words=
echo "== scissor 20x20 dynamic: ISP scissor enabled"
VK_GEOM_DYNSC=1 SX=0 SY=0 SW=20 SH=20 timeout 60 ./vk_geom64 2>/dev/null | grep words=
systemctl start greetd
echo DONE
