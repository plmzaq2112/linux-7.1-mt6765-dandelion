#!/bin/sh
# Compare vendor vs Mesa HWRTData + 3D command stream at 720x1600.
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
  echo RESTORED
}
trap restore EXIT INT TERM

systemctl stop greetd
sleep 3
pkill -f phoc 2>/dev/null
sleep 1

rmmod pvrsrvkm || { echo "rmmod failed"; exit 1; }
sleep 1
insmod "$MOD_DEBUG" || { echo "insmod debug (no args) failed"; insmod "$MOD_DEBUG" pvr_apm=0 || { echo "insmod failed"; exit 1; }; }
sleep 1
lsmod | grep pvrsrvkm

# ---------- vendor ----------
echo 4 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick 2>/dev/null
dmesg -C 2>/dev/null
cd /root || exit 1
export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw
timeout 60 /root/gles_clear 720 1600 1 0 0 >/tmp/vendor_out.txt 2>&1
sleep 1
dmesg > /tmp/dmesg_vendor.txt 2>/dev/null
echo "vendor hwrt lines: $(grep -c 'pvr-hwrt' /tmp/dmesg_vendor.txt)"
echo "vendor dump lines: $(grep -c 'pvr-dump' /tmp/dmesg_vendor.txt)"

# ---------- mesa ----------
echo 4 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick 2>/dev/null
dmesg -C 2>/dev/null
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
unset EGL_LIB GLES_LIB
timeout 90 ./vk_geom720 >/tmp/mesa_out.txt 2>&1
sleep 1
dmesg > /tmp/dmesg_mesa.txt 2>/dev/null
echo "mesa hwrt lines: $(grep -c 'pvr-hwrt' /tmp/dmesg_mesa.txt)"
echo "mesa dump lines: $(grep -c 'pvr-dump' /tmp/dmesg_mesa.txt)"

echo "=== vendor hwrt ==="
grep 'pvr-hwrt' /tmp/dmesg_vendor.txt | tail -3
echo "=== mesa hwrt ==="
grep 'pvr-hwrt' /tmp/dmesg_mesa.txt | tail -3
