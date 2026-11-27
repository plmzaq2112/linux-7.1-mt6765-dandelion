#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
systemctl stop greetd
sleep 3
run() {
  echo "=== $1 ==="
  shift
  env "$@" timeout 60 ./vk_ds 2>/dev/null | grep -E 'color:|depth:|center='
}
run "D16 baseline"
run "D16 bgobjdepth=float1" PVR13_BGOBJDEPTH=0x3f800000
run "D16 zls_stride=0" PVR13_ZLSSTRIDE=0
run "D16 bgobjdepth=float1 + stride=0" PVR13_BGOBJDEPTH=0x3f800000 PVR13_ZLSSTRIDE=0
run "D16 bgobjdepth=float1 + stride=0 + zlsctl=f32" PVR13_BGOBJDEPTH=0x3f800000 PVR13_ZLSSTRIDE=0 PVR13_ZLSCTL=0x1808001c
systemctl start greetd
echo DONE
