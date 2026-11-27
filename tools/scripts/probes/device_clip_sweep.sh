#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
run() {
  bin=$1
  name=$2
  shift 2
  env "$@" ./$bin >/tmp/g_$name.out 2>/tmp/g_$name.err
  echo "== $name | $(grep -h 'words=' /tmp/g_$name.out) | $(grep -h 'bbox' /tmp/g_$name.out)"
}
run vk_geom64 t0
run vk_geom64 r4 PVR13_RGN_R=4 PVR13_RGN_B=4
run vk_geom64 r4t4 PVR13_RGN_R=4 PVR13_RGN_B=4 PVR13_TERM_R=4 PVR13_TERM_B=4
run vk_geom64 r3t4 PVR13_TERM_R=4 PVR13_TERM_B=4
run vk_geom64 r5t4 PVR13_RGN_R=5 PVR13_RGN_B=5 PVR13_TERM_R=4 PVR13_TERM_B=4
run vk_geom32 s0
run vk_geom32 s2 PVR13_RGN_R=2 PVR13_RGN_B=2 PVR13_TERM_R=2 PVR13_TERM_B=2
echo ALLDONE
