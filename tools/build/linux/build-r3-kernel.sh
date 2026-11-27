#!/bin/bash
# r3 kernel build: drop every legacy (auto-binding) USB gadget driver so the
# configfs ACM gadget can own the UDC.
set -e
cd "$HOME/AI Project/Redmi 9A/kernel 7.1 mainline" || exit 1

LEGACY="USB_ETH USB_G_HID USB_MIDI USB_G_WEBCAM USB_G_DBGP USB_G_SERIAL \
USB_G_MULTI USB_G_NCM USB_G_PRINTER USB_G_ACM_MS USB_ZERO USB_MASS_STORAGE \
USB_FUNCTIONFS USB_RAW_GADGET"
for s in $LEGACY; do
  scripts/config --file arch/arm64/configs/dandelion_defconfig -d "$s" || true
done

make ARCH=arm64 O=out dandelion_defconfig >/dev/null
make ARCH=arm64 O=out olddefconfig >/dev/null
echo "=== legacy gadget drivers still enabled in out/.config ==="
grep -E '^CONFIG_USB_(ETH|G_HID|MIDI|G_WEBCAM|G_DBGP|G_SERIAL|G_MULTI|G_NCM|G_PRINTER|G_ACM_MS|ZERO|MASS_STORAGE|FUNCTIONFS|RAW_GADGET)=' out/.config || echo "(none)"
echo "=== configfs ACM ==="
grep -E '^CONFIG_USB_(CONFIGFS|CONFIGFS_ACM|F_ACM)=' out/.config

echo "=== building Image ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- O=out -j8 Image
gzip -9 -c out/arch/arm64/boot/Image > out/arch/arm64/boot/Image.gz
ls -l out/arch/arm64/boot/Image out/arch/arm64/boot/Image.gz
cat out/include/config/kernel.release
echo "=== build done ==="
