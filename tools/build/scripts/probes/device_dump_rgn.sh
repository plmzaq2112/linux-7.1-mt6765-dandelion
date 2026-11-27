#!/bin/sh
# Dump TA-written region headers for vendor and Mesa at 720x1600.
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
lsmod | grep pvrsrvkm

# ---------- vendor ----------
echo 4 > /sys/module/pvrsrvkm/parameters/pvr_dump_rgn 2>/dev/null || echo "param missing"
dmesg -C 2>/dev/null
cd /root || exit 1
export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw
export GLES_LOOP=3
timeout 90 /root/gles_clear 720 1600 1 0 0 >/tmp/vendor_rgn_out.txt 2>&1
sleep 1
dmesg > /tmp/rgn_vendor.txt 2>/dev/null

# ---------- mesa ----------
echo 4 > /sys/module/pvrsrvkm/parameters/pvr_dump_rgn 2>/dev/null
dmesg -C 2>/dev/null
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=3
unset EGL_LIB GLES_LIB
timeout 120 ./vk_geom720 >/tmp/mesa_rgn_out.txt 2>&1
sleep 1
dmesg > /tmp/rgn_mesa.txt 2>/dev/null

echo "=== vendor rgn lines ==="
grep -c 'pvr-rgn' /tmp/rgn_vendor.txt
echo "=== mesa rgn lines ==="
grep -c 'pvr-rgn' /tmp/rgn_mesa.txt
