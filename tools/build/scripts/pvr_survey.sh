#!/bin/bash
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== mesa-pvr ==="
ls -d "$M" 2>/dev/null && ls "$M" | head -12
echo "build dirs:"
ls -d "$M"/build-* 2>/dev/null
echo
echo "=== mesa git status ==="
cd "$M" 2>/dev/null && git status --porcelain | head -20
echo
echo "=== libvulkan build ==="
ls -l "$M"/build-arm64/src/imagination/vulkan/libvulkan_powervr_mesa.so 2>/dev/null
echo
echo "=== cross files ==="
ls -l /tmp/arm64-cross.txt /tmp/arm64-pkg-config 2>/dev/null || echo "cross files missing"
echo
echo "=== kernel pvr dump hook ==="
grep -n "pvr_dump_kick" "$T"/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxta3d.c | head -6
grep -n "pvr_dump_kick" "$T"/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxtransfer.c | head -4
echo
echo "=== porting docs ==="
ls -l "$T"/docs/porting/ | head
