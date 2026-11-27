#!/bin/sh
echo "=== libwlroots version ==="
apk info -v wlroots 2>/dev/null || true
ls -l /usr/lib/aarch64-linux-gnu/libwlroots.so.12
echo "=== wlroots vulkan hints ==="
strings -a /usr/lib/aarch64-linux-gnu/libwlroots.so.12 2>/dev/null | grep -iE "vulkan|WLR_RENDERER" | sort -u | head -25
echo "=== phoc hints ==="
strings -a /usr/bin/phoc 2>/dev/null | grep -iE "WLR_RENDERER|vulkan|renderer" | sort -u | head -20
echo "=== greetd config ==="
cat /etc/greetd/config.toml 2>/dev/null | head -20
echo "=== bridge dir ==="
ls -l /usr/local/bin 2>/dev/null | head -20
