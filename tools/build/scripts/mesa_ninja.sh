#!/bin/bash
cd /home/a12bbb/AI_Project/Redmi_9A/mesa-pvr || exit 1
PATH="$PWD/build-native/src/compiler/clc:$PWD/build-native/src/compiler/spirv:$PWD/build-native/src/imagination/pco/uscgen:$PWD/build-native/src/imagination/pdsc:$PATH"
export PATH
ninja -C build-arm64 src/imagination/vulkan/libvulkan_powervr_mesa.so 2>&1 | head -40
