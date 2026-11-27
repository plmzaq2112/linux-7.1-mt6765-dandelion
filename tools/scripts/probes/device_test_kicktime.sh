#!/bin/sh
MOD_NEW=/root/pvrsrvkm-kicktime.ko
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

systemctl stop greetd
sleep 3
pkill -f phoc 2>/dev/null
sleep 1

rmmod pvrsrvkm || { echo "rmmod failed"; exit 1; }
sleep 1
insmod "$MOD_NEW" || { echo "insmod (no args) failed"; insmod "$MOD_NEW" pvr_apm=0 || { echo "insmod failed"; exit 1; }; }
sleep 1
lsmod | grep pvrsrvkm

echo 8 > /sys/module/pvrsrvkm/parameters/pvr_kick_time 2>/dev/null || echo "param missing"
cat /sys/module/pvrsrvkm/parameters/pvr_kick_time

cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export VK_KMS_SECS=3
dmesg -C 2>/dev/null
timeout 60 ./vk_kms2 2>&1 | tail -3
sleep 1
echo "=== pvr-kick timings ==="
timeout 10 dmesg | grep 'pvr-kick' | tail -40
