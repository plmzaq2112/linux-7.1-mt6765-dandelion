#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
run() {
  bin=$1
  shift
  env "$@" ./$bin >/tmp/f_$bin.out 2>/tmp/f_$bin.err
  echo "== $bin $* | $(grep -h 'words=' /tmp/f_$bin.out) | $(grep -h 'bbox' /tmp/f_$bin.out)"
}
run vk_geom64
run vk_geom128
run vk_geom256
run vk_geom320x480
run vk_geom720x1600
run vk_geom64 PVR13_MTILE_FULL=1
run vk_geom128 PVR13_MTILE_FULL=1
run vk_geom256 PVR13_MTILE_FULL=1
run vk_geom320x480 PVR13_MTILE_FULL=1
run vk_geom720x1600 PVR13_MTILE_FULL=1
echo ALLDONE
