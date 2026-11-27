#!/bin/sh
cd /root || exit 1
export EGL_LIB=libEGL.so.1
export GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw
export GLES_LOOP=20
systemctl stop greetd
sleep 3
echo "=== vendor 720x1600 clear loop ==="
timeout 180 /root/gles_clear 720 1600 1 0 0 2>/dev/null | grep -E 'bench|clear 720'
echo "=== vendor 64x64 clear loop ==="
timeout 120 /root/gles_clear 64 64 1 0 0 2>/dev/null | grep -E 'bench|clear 64'
systemctl start greetd
echo DONE
