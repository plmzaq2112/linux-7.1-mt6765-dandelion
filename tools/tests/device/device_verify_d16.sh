#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
systemctl stop greetd
sleep 3
echo "=== D16 (after quirk) ==="
timeout 60 ./vk_ds 2>/dev/null | tail -4
echo "=== D32_SFLOAT (regression) ==="
VK_DS_D32=1 timeout 60 ./vk_ds 2>/dev/null | tail -4
echo "=== other regressions ==="
timeout 60 ./vk_colored_quad 2>/dev/null | grep words=
timeout 60 ./vk_textured_quad 2>/dev/null | grep words=
timeout 60 ./vk_clear2 2>/dev/null | grep words=
VK_GEOM_LOOP=5 timeout 120 ./vk_geom720 2>/dev/null | grep -E 'bench|words='
systemctl start greetd
echo DONE
