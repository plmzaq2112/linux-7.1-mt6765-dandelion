#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export PVR13_DUMP_RT=1
run() {
  bin=$1
  ./$bin >/tmp/o_$bin.out 2>/tmp/o_$bin.err
  echo "== $bin rc=$? | $(grep -h 'words=' /tmp/o_$bin.out) | $(grep -h 'bbox' /tmp/o_$bin.out)"
  grep -h 'pvr-rt:' /tmp/o_$bin.err | tail -1
}
run vk_geom64
run vk_geom32
run vk_geom128
run vk_geom256
run vk_geom320x480
run vk_geom720x1600
run vk_colored_quad
run vk_textured_quad
run vk_clear2
run vk_clear2_32
echo ALLDONE
