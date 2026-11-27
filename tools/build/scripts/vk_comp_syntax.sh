#!/bin/bash
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
aarch64-linux-gnu-gcc -fsyntax-only -I "$W/logs" -I "$M/include" -I /usr/include/libdrm \
    "$W/src/wayland/vk_comp.c" 2>&1 | head -20
echo "=== tail ==="
tail -12 "$W/src/wayland/vk_comp.c"
