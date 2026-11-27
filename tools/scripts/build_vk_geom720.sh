#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"

aarch64-linux-gnu-gcc -O1 -g0 -DW=720 -DH=1600 -I "$L" -I "$M/include" \
    "$W/src/wayland/vk_geom.c" "$L/libvulkan.so.1" \
    -o "$W/logs/vk_geom720"
ls -l "$W/logs/vk_geom720"
