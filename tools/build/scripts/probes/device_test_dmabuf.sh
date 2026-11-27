#!/bin/sh
# Test the PVR dma-buf export ops: swap in the patched pvrsrvkm, run vk_kms
# with zero-copy scanout, then always restore the daily module + greetd.
MOD_NEW=/root/pvrsrvkm-dmabuf.ko
MOD_ORIG=/root/pvrsrvkm.ko.orig

restore() {
  echo "=== restore ==="
  rmmod pvrsrvkm 2>/dev/null
  sleep 1
  insmod "$MOD_ORIG" pvr_apm=0 2>/dev/null || insmod "$MOD_ORIG" 2>/dev/null
  sleep 1
  systemctl start greetd 2>/dev/null
  lsmod | grep pvrsrvkm
  echo RESTORED
}
trap restore EXIT INT TERM

echo "=== installed module (reboot fallback) ==="
modinfo -n pvrsrvkm 2>/dev/null | head -2

systemctl stop greetd
sleep 3
pkill -f phoc 2>/dev/null
sleep 1

rmmod pvrsrvkm || { echo "rmmod failed"; exit 1; }
sleep 1
insmod "$MOD_NEW" || { echo "insmod (no args) failed"; insmod "$MOD_NEW" pvr_apm=0 || { echo "insmod failed"; exit 1; }; }
sleep 1
lsmod | grep pvrsrvkm

cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export VK_KMS_SECS=15
timeout 90 ./vk_kms 2>&1 | tail -20
echo "vk_kms rc=$?"
echo "=== dmesg (pvr-dmabuf) ==="
timeout 10 dmesg | grep 'pvr-dmabuf' | tail -8
echo "=== dmesg (mtk/drm errors) ==="
timeout 10 dmesg | grep -iE 'mtk-drm|drm.*(error|fail)|prime' | tail -8
