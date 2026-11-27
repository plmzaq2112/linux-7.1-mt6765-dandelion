#!/bin/bash
cd "$HOME/AI Project/Redmi 9A/kernel 7.1 mainline" || exit 1
for k in FB_SIMPLE FRAMEBUFFER_CONSOLE DRM_MEDIATEK SERIAL_8250_MT6577 USB_MTU3 USB_F_ACM USB_CONFIGFS_ACM PSTORE_RAM PSTORE_CONSOLE PSTORE_PMSG USB_CONFIGFS USB_GADGET USB_ETH USB_G_HID; do
  line=$(grep -E "^(# )?CONFIG_${k}[= ]" arch/arm64/configs/dandelion_defconfig | head -1)
  printf '%-24s %s\n' "$k" "${line:-<absent>}"
done
