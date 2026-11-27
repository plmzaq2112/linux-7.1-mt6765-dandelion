#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
run() {
  bin=$1
  ./$bin >/tmp/m_$bin.out 2>/tmp/m_$bin.err
  echo "== $bin rc=$? | $(grep -h 'words=' /tmp/m_$bin.out) | $(grep -h 'bbox' /tmp/m_$bin.out)"
}
run vk_geom64
run vk_geom32
run vk_geom128
run vk_geom256
run vk_geom320x480
run vk_geom720x1600
run vk_colored_quad
run vk_textured_quad
echo ALLDONE
