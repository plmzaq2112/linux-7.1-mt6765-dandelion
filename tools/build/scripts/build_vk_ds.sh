#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"

glslangValidator -V "$W/scripts/ds.vert" -o "$L/ds.vert.spv"
glslangValidator -V "$W/scripts/ds.frag" -o "$L/ds.frag.spv"
python3 "$W/scripts/spv_to_header.py" ds_vert_spv "$L/ds.vert.spv" "$L/ds_vert_spv.h"
python3 "$W/scripts/spv_to_header.py" ds_frag_spv "$L/ds.frag.spv" "$L/ds_frag_spv.h"

aarch64-linux-gnu-gcc -O1 -g0 -I "$L" -I "$M/include" \
    "$W/src/wayland/vk_ds.c" "$L/libvulkan.so.1" -o "$L/vk_ds"
ls -l "$L/vk_ds"
