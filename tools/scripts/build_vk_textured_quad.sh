#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"

glslangValidator -V "$W/scripts/quad.vert" -o "$L/quad.vert.spv"
glslangValidator -V "$W/scripts/quad.frag" -o "$L/quad.frag.spv"
python3 "$W/scripts/spv_to_header.py" quad_vert_spv "$L/quad.vert.spv" "$L/quad_vert_spv.h"
python3 "$W/scripts/spv_to_header.py" quad_frag_spv "$L/quad.frag.spv" "$L/quad_frag_spv.h"

aarch64-linux-gnu-gcc -O1 -g0 -I "$L" -I "$M/include" \
    "$W/src/wayland/vk_textured_quad.c" "$W/logs/libvulkan.so.1" \
    -o "$W/logs/vk_textured_quad"
ls -l "$W/logs/vk_textured_quad"
