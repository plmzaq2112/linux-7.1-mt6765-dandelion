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
cd /root || exit 1
export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw
timeout 90 /root/gles_depth 64 64 >/tmp/gles_depth_out.txt 2>&1
sleep 1
cat /tmp/gles_depth_out.txt | tail -2
dmesg > /tmp/ds_vendor_kick.txt 2>/dev/null
echo "3D lines: $(grep -c 'pvr-dump-3D' /tmp/ds_vendor_kick.txt)"
grep 'pvr-dump-3D' /tmp/ds_vendor_kick.txt | head -22
