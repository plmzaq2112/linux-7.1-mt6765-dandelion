#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=15
systemctl stop greetd
sleep 3
for lg in 12 14 16 18; do
  echo "=== page log2=$lg ==="
  PVR13_PAGE_LOG2=$lg timeout 180 ./vk_geom720 2>/dev/null | grep -E 'bench|pvr-page' | tail -2
done
systemctl start greetd
echo DONE
