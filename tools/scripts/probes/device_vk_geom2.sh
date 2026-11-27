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
  echo "== $name | $(grep -h 'viewport=' /tmp/g_$name.err) | $(grep -h 'words=' /tmp/g_$name.out) | $(grep -h 'bbox' /tmp/g_$name.out)"
}
run vk_geom64 m64
run vk_geom32 m32
chmod +x ./vk_geom64 ./vk_geom32 2>/dev/null
run vk_geom64 m64
run vk_geom32 m32
echo ALLDONE
