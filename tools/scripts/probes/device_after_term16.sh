#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
run() {
  bin=$1
  shift
  env "$@" ./$bin >/tmp/r_$bin.out 2>/tmp/r_$bin.err
  echo "== $bin rc=$? | $(grep -h 'words=' /tmp/r_$bin.out) | $(grep -h 'bbox' /tmp/r_$bin.out)"
}
run vk_geom64
run vk_geom32
run vk_triangle
run vk_colored_quad
run vk_textured_quad
grep -h '(0,0)=' /tmp/r_vk_colored_quad.out
grep -h '(0,0)=' /tmp/r_vk_textured_quad.out
echo ALLDONE
