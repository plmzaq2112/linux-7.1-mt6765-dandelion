#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"

glslangValidator -V "$W/src/wayland/comp.vert" -o "$L/comp.vert.spv"
glslangValidator -V "$W/src/wayland/comp.frag" -o "$L/comp.frag.spv"
python3 "$W/scripts/spv_to_header.py" comp_vert_spv "$L/comp.vert.spv" "$L/comp_vert_spv.h"
python3 "$W/scripts/spv_to_header.py" comp_frag_spv "$L/comp.frag.spv" "$L/comp_frag_spv.h"

aarch64-linux-gnu-gcc -O2 -g0 -I "$L" -I "$M/include" -I /usr/include/libdrm \
    "$W/src/wayland/vk_comp.c" "$L/libvulkan.so.1" \
    -L /usr/lib/aarch64-linux-gnu -ldrm -lm \
    -o "$L/vk_comp"
ls -l "$L/vk_comp"
