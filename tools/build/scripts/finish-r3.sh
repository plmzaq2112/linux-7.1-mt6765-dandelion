#!/bin/bash
set -e
cd "$HOME/AI Project/Redmi 9A/kernel 7.1 mainline"/out || exit 1
echo "=== key config ==="
for k in USB_CONFIGFS USB_CONFIGFS_ACM USB_F_ACM USB_MTU3 FB_SIMPLE FRAMEBUFFER_CONSOLE PSTORE_RAM PSTORE_CONSOLE PSTORE_PMSG USB_GADGET; do
  printf '%-24s %s\n' "$k" "$(grep -E "^(# )?CONFIG_${k}[= ]" .config | head -1)"
done
echo "=== legacy gadget drivers (should be absent / not set) ==="
grep -E '^CONFIG_USB_(ETH|G_HID|G_SERIAL|MASS_STORAGE|ZERO|FUNCTIONFS|RAW_GADGET)=' .config || echo "(none enabled)"
echo "=== packing r3 ==="
bash "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"/installer/linux/build-boot-r3.sh
