#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
P="$W/kernel/patches/kernel-untracked-files"
mkdir -p "$P"
K=/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline
cp "$K/drivers/leds/regulator-vibrator.c" "$P/" 2>/dev/null || true
cp "$K/drivers/misc/rail_en.c" "$P/" 2>/dev/null || true
ls -l "$P"
rm -f "$W/scripts/archive_probe.sh" "$W/scripts/archive_probe2.sh" \
      "$W/scripts/archive_probe3.sh" "$W/scripts/archive_verify.sh" \
      "$W/scripts/archive_snapshot.sh"
echo "temp probe scripts removed"
