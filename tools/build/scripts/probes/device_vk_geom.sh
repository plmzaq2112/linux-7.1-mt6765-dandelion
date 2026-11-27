#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
run() {
  name=$1
  shift
  env "$@" ./vk_geom >/tmp/g_$name.out 2>/tmp/g_$name.err
  echo "== $name | $(grep -h 'viewport=' /tmp/g_$name.err) | $(grep -h 'words=' /tmp/g_$name.out) | $(grep -h 'bbox' /tmp/g_$name.out)"
}
run a
run b VW=32 VH=32
run c SW=16 SH=16
run d SX=32 SY=32 SW=32 SH=32
run e VW=32 VH=64
echo ALLDONE
