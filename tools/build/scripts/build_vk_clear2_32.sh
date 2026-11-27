#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
aarch64-linux-gnu-gcc -O1 -g0 -DW=32 -DH=32 -I "$M/include" \
    "$W/src/wayland/vk_clear2.c" "$W/logs/libvulkan.so.1" \
    -o "$W/logs/vk_clear2_32"
ls -l "$W/logs/vk_clear2_32"
