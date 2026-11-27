#!/bin/sh
cd /root || exit 1
export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw
export GLES_LOOP=15
systemctl stop greetd
sleep 3
echo "=== vendor 3D draw 720x1600 ==="
timeout 180 /root/gles_triangle 720 1600 2>/dev/null | grep -E 'bench|triangle 720'
echo "=== vendor 3D draw 64x64 ==="
timeout 120 /root/gles_triangle 64 64 2>/dev/null | grep -E 'bench|triangle 64'
systemctl start greetd
echo DONE
