#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
aarch64-linux-gnu-gcc -O1 -g0 -I "$M/include" \
    "$W/src/wayland/vk_clear_tq.c" "$W/logs/libvulkan.so.1" \
    -o "$W/logs/vk_clear_tq"
ls -l "$W/logs/vk_clear_tq"
