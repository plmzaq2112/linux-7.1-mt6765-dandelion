#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"

glslangValidator -V "$W/scripts/color.vert" -o "$L/color.vert.spv"
glslangValidator -V "$W/scripts/color.frag" -o "$L/color.frag.spv"
python3 "$W/scripts/spv_to_header.py" color_vert_spv "$L/color.vert.spv" "$L/color_vert_spv.h"
python3 "$W/scripts/spv_to_header.py" color_frag_spv "$L/color.frag.spv" "$L/color_frag_spv.h"

aarch64-linux-gnu-gcc -O1 -g0 -I "$L" -I "$M/include" \
    "$W/src/wayland/vk_colored_quad.c" "$W/logs/libvulkan.so.1" \
    -o "$W/logs/vk_colored_quad"
ls -l "$W/logs/vk_colored_quad"
