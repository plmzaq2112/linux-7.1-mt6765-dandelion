#!/bin/bash
set -e
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
cd "$M"
cp /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/scripts/arm64-cross.txt /tmp/arm64-cross.txt
export PATH="$M/build-native/src/compiler/clc:$M/build-native/src/compiler/spirv:$M/build-native/src/imagination/pco/uscgen:$M/build-native/src/imagination/pdsc:$PATH"
ninja -C build-arm64 src/imagination/vulkan/libvulkan_powervr_mesa.so 2>&1 | tail -5
OUT=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/libvulkan_powervr_mesa.so
aarch64-linux-gnu-strip -s build-arm64/src/imagination/vulkan/libvulkan_powervr_mesa.so -o "$OUT"
ls -l "$OUT"
