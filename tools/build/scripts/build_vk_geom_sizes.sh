#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"
build() {
  name=$1
  w=$2
  h=$3
  aarch64-linux-gnu-gcc -O1 -g0 -DW=$w -DH=$h -I "$L" -I "$M/include" \
      "$W/src/wayland/vk_geom.c" "$L/libvulkan.so.1" -o "$L/$name"
  echo "$name $(stat -c %s "$L/$name")"
}
build vk_geom128 128 128
build vk_geom256 256 256
build vk_geom720x1600 720 1600
build vk_geom320x480 320 480
