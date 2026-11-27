#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
run() {
  bin=$1
  ./$bin >/tmp/s_$bin.out 2>/tmp/s_$bin.err
  echo "== $bin rc=$? | $(grep -h 'words=' /tmp/s_$bin.out) | $(grep -h 'bbox' /tmp/s_$bin.out)"
}
run vk_geom128
run vk_geom256
run vk_geom320x480
run vk_geom720x1600
echo ALLDONE
