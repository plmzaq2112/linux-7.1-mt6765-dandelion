#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=10
systemctl stop greetd
sleep 3
echo "=== baseline ==="
timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== flags 0x130 = 0 ==="
PVR13_3D_FLAGS0=1 timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== isp_ctl = 0x3600f (vendor) ==="
PVR13_ISPCTL=0x3600f timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== isp_ctl=0x3600f + flags0 + bgobj=0x100 ==="
PVR13_ISPCTL=0x3600f PVR13_3D_FLAGS0=1 PVR13_BGobjVALS=0x100 timeout 180 ./vk_geom720 2>/dev/null | grep bench
systemctl start greetd
echo DONE
