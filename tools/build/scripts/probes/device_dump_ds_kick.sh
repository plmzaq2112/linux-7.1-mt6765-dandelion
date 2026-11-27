#!/bin/sh
MOD_DEBUG=/root/pvrsrvkm-rgn.ko
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
insmod "$MOD_DEBUG" || { insmod "$MOD_DEBUG" pvr_apm=0 || { echo "insmod failed"; exit 1; }; }
sleep 1

echo 8 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick 2>/dev/null
dmesg -C 2>/dev/null
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
timeout 60 ./vk_ds >/tmp/ds_out.txt 2>&1
sleep 1
dmesg > /tmp/ds_kick.txt 2>/dev/null
echo "kick dumps: $(grep -c 'pvr-dump-3D' /tmp/ds_kick.txt)"
grep -E 'pvr-dump: KickTA3D|pvr-dump-3D' /tmp/ds_kick.txt | head -24
