#!/bin/sh
cd /tmp/pvr-vk || exit 1
systemctl stop greetd
sleep 3

echo "=== Mesa: draw-count scaling (720x1600, 3D pass) ==="
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_GEOM_LOOP=10
for n in 1 4 16 64 256; do
  printf "  draws=%-4s " "$n"
  VK_GEOM_DRAWS=$n timeout 180 ./vk_geom720 2>/dev/null | grep bench | sed 's/bench 720x1600: //'
done

echo "=== Vendor: draw-count scaling (720x1600) ==="
export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw
export GLES_LOOP=10
for n in 1 4 16 64 256; do
  printf "  draws=%-4s " "$n"
  GLES_DRAWS=$n timeout 180 /root/gles_triangle 720 1600 2>/dev/null | grep bench | sed 's/gles tri bench 720x1600: //'
done

systemctl start greetd
echo DONE
