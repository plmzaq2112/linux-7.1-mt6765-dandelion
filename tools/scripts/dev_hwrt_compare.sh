#!/bin/sh
# Compare the vendor GLES (1.13 UM) and Mesa HWRTData creation parameters.
systemctl stop greetd 2>/dev/null
sleep 2
rmmod pvrsrvkm 2>/dev/null
sleep 1
insmod /root/pvrsrvkm-hwrt.ko pvr_apm=0
sleep 1

echo "=== vendor GLES 64x64 clear ==="
export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw
dmesg -C
/root/gles_clear 64 64 1 0 0 2>&1 | tail -1
sleep 1
dmesg | grep "pvr-hwrt:" | tail -3

echo "=== mesa vk_clear2 ==="
dmesg -C
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
timeout 20 ./vk_clear2 > clear2.log 2>&1
sleep 1
dmesg | grep "pvr-hwrt:" | tail -3
grep -E "words=|first32" clear2.log | head -3
