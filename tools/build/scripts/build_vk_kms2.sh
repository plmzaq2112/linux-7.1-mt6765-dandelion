#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"
aarch64-linux-gnu-gcc -O2 -g0 -I "$L" -I "$M/include" -I /usr/include/libdrm \
    "$W/src/wayland/vk_kms2.c" "$L/libvulkan.so.1" \
    -L /usr/lib/aarch64-linux-gnu -ldrm -lm \
    -o "$L/vk_kms2"
ls -l "$L/vk_kms2"
