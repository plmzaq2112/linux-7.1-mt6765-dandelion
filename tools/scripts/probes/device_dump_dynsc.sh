#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export PVR_DEBUG=cs
systemctl stop greetd
sleep 3
echo "=== dynamic scissor 32x32 ==="
VK_GEOM_DYNSC=1 SX=0 SY=0 SW=32 SH=32 timeout 120 ./vk_geom64 > /tmp/dynsc_out.txt 2>&1
grep -E 'words=|bbox|STATE_HEADER|pres_region_clip|pres_viewport|left|right|top|bottom|scindex|dbindex|scenable|STATE_ISPCTL' /tmp/dynsc_out.txt | head -30
echo "=== static scissor 32x32 (reference) ==="
SX=0 SY=0 SW=32 SH=32 timeout 120 ./vk_geom64 > /tmp/statsc_out.txt 2>&1
grep -E 'words=|bbox|pres_region_clip|left|right|top|bottom|scindex|dbindex|scenable' /tmp/statsc_out.txt | head -30
systemctl start greetd
echo DONE
