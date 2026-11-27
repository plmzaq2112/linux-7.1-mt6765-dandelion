#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"
aarch64-linux-gnu-gcc -O1 -g0 -I "$M/include" "$W/src/wayland/vk_clear_tq.c" "$L/libvulkan.so.1" -o "$L/vk_clear_tq64"
aarch64-linux-gnu-gcc -O1 -g0 -DW=720 -DH=1600 -I "$M/include" "$W/src/wayland/vk_clear_tq.c" "$L/libvulkan.so.1" -o "$L/vk_clear_tq720"
ls -l "$L/vk_clear_tq64" "$L/vk_clear_tq720"
