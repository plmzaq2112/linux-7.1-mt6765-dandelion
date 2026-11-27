#!/bin/sh
. /etc/os-release 2>/dev/null
echo "os=$PRETTY_NAME"
echo "=== packages ==="
dpkg -l 2>/dev/null | grep -E 'wlroots|sway|labwc|weston|phoc|phosh' | head -14
echo "=== dri ==="
ls /dev/dri/ 2>/dev/null
echo "=== vulkan libs ==="
ls /usr/lib/aarch64-linux-gnu/libvulkan* 2>/dev/null
echo "=== icd dir ==="
ls /usr/share/vulkan/icd.d/ 2>/dev/null
echo "=== drm tools ==="
which modetest kmscube 2>/dev/null
