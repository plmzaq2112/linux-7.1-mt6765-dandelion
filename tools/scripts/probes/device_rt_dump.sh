#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export PVR13_DUMP_RT=1
for b in vk_geom64 vk_geom128 vk_geom320x480 vk_geom720x1600; do
  ./$b >/tmp/d_$b.out 2>/tmp/d_$b.err
  echo "== $b $(grep -h 'words=' /tmp/d_$b.out) | $(grep -h 'bbox' /tmp/d_$b.out)"
  grep -h 'pvr-rt:' /tmp/d_$b.err | head -3
done
echo ALLDONE
