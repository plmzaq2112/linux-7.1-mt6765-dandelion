#!/bin/sh
# Vendor golden HWRTData capture for a real 720x1600 target.
# Swaps in the instrumented pvrsrvkm module, runs vendor GLES clear, then
# restores the original module and greetd.

MOD_DEBUG=/root/pvrsrvkm-hwrt.ko
MOD_ORIG=/root/pvrsrvkm.ko.orig

restore() {
  echo "=== restore ==="
  rmmod pvrsrvkm 2>/dev/null
  sleep 1
  insmod "$MOD_ORIG" pvr_apm=0 2>/dev/null || insmod "$MOD_ORIG" 2>/dev/null
  sleep 1
  systemctl start greetd 2>/dev/null
  lsmod | grep pvrsrvkm
  echo "RESTORED"
}
trap restore EXIT INT TERM

echo "=== stop greetd ==="
systemctl stop greetd
sleep 3
pkill -f phoc 2>/dev/null
sleep 1

echo "=== swap module ==="
rmmod pvrsrvkm || { echo "rmmod failed"; exit 1; }
sleep 1
insmod "$MOD_DEBUG" || { echo "insmod debug (no args) failed"; insmod "$MOD_DEBUG" pvr_apm=0 || { echo "insmod debug failed"; exit 1; }; }
sleep 1
lsmod | grep pvrsrvkm

export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw

dmesg -C
echo "=== vendor gles_clear 720x1600 ==="
timeout 60 /root/gles_clear 720 1600 1 0 0 2>&1 | tail -3
sleep 1
echo "=== pvr-hwrt (vendor) ==="
dmesg | grep -E 'pvr-hwrt' | head -20
echo "=== done ==="
