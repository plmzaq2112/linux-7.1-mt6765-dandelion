#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
cp "$W/logs/vk_geom" "$W/logs/vk_geom64"
EXTRA_CFLAGS="-DW=32 -DH=32" bash "$W/scripts/build_vk_geom.sh"
cp "$W/logs/vk_geom" "$W/logs/vk_geom32"
stat -c '%n %s' "$W/logs/vk_geom64" "$W/logs/vk_geom32"
