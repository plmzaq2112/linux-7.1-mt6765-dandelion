#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
gcc -O0 -std=c11 \
    -I "$M/src/imagination/vulkan/winsys/pvrsrvkm" \
    -I "$M/src/imagination/vulkan/winsys" \
    -I "$M/src/imagination/vulkan" \
    -I "$M/src/imagination" \
    -I "$M/src/imagination/include" \
    -I "$M/src/imagination/common" \
    -I "$M/src/vulkan/runtime" \
    -I "$M/src/vulkan/util" \
    -I "$M/src/util" \
    -I "$M/src" \
    -I "$M/include" \
    "$W/scripts/mesa_offsets.c" -o /tmp/mesa_offsets 2>&1 | head -20
/tmp/mesa_offsets
