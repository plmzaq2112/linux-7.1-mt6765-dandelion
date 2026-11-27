#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=15
systemctl stop greetd
sleep 3
echo "=== clear + draw ==="
timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== clear only (no draw) ==="
VK_GEOM_NODRAW=1 timeout 180 ./vk_geom720 2>/dev/null | grep bench
echo "=== draw only (no clear) ==="
VK_GEOM_NOCLEAR=1 timeout 180 ./vk_geom720 2>/dev/null | grep bench
systemctl start greetd
echo DONE
