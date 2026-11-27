#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=10
systemctl stop greetd
sleep 3
for v in "" 6 0 8; do
  if [ -z "$v" ]; then
    echo "=== default (5) ==="
    timeout 180 ./vk_geom720 2>/dev/null | grep -E 'bench|words='
  else
    echo "=== region_stride=$v ==="
    PVR13_RGN_STRIDE=$v timeout 180 ./vk_geom720 2>/dev/null | grep -E 'bench|words='
  fi
done
systemctl start greetd
echo DONE
