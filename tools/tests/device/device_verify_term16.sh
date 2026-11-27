#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
run() {
  bin=$1
  shift
  env "$@" ./$bin >/tmp/v_$bin.out 2>/tmp/v_$bin.err
  echo "== $bin rc=$? | $(grep -h 'words=' /tmp/v_$bin.out) | $(grep -h 'bbox' /tmp/v_$bin.out)"
}
run vk_geom720
run vk_clear2
run vk_clear2_32
run vk_clear_tq
grep -h . /tmp/v_clear2.out 2>/dev/null | head -3
echo ALLDONE
