#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=10
systemctl stop greetd
sleep 3
echo "=== 720x1600 after rgn alignment fix ==="
timeout 180 ./vk_geom720 2>/dev/null | grep -E 'bench|words='
echo "=== 64x64 after fix ==="
timeout 120 ./vk_geom64 2>/dev/null | grep -E 'bench|words='
systemctl start greetd
echo DONE
