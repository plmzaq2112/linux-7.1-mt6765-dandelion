#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"

glslangValidator -V "$W/scripts/tri.vert" -o "$L/tri.vert.spv"
glslangValidator -V "$W/scripts/tri.frag" -o "$L/tri.frag.spv"
python3 "$W/scripts/spv_to_header.py" tri_vert_spv "$L/tri.vert.spv" "$L/tri_vert_spv.h"
python3 "$W/scripts/spv_to_header.py" tri_frag_spv "$L/tri.frag.spv" "$L/tri_frag_spv.h"

aarch64-linux-gnu-gcc -O1 -g0 -I "$L" -I "$M/include" \
    "$W/src/wayland/vk_triangle.c" "$W/logs/libvulkan.so.1" \
    -o "$W/logs/vk_triangle"
ls -l "$W/logs/vk_triangle"
