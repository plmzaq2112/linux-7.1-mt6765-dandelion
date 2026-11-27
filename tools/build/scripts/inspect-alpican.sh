#!/bin/bash
set -u
cd "$HOME"
rm -rf alpican-gpu
mkdir -p alpican-gpu
tar -xzf alpican-gpu.tar.gz -C alpican-gpu --strip-components=1 || { echo "extract failed"; exit 1; }
cd alpican-gpu
echo "== kernel version =="
head -4 Makefile
echo "== gpu dirs =="
ls drivers/gpu/mediatek 2>/dev/null | head
echo "== defconfig gpu =="
grep -h -e MTK_GPU -e FW_LOADER_USER_HELPER arch/arm64/configs/*defconfig 2>/dev/null | sort -u | head -20
echo "== fw refs =="
grep -rn -e 'rgx.fw' -e 'rgx.sh' drivers/gpu/mediatek 2>/dev/null | head -5
echo "== dts gpu nodes =="
grep -rln -e 'mediatek,doma' -e 'gpu@13000000' arch/arm64/boot/dts/mediatek/ 2>/dev/null | head -5
echo "== pvr dirs =="
ls drivers/gpu/mediatek/gpu_rgx 2>/dev/null | head
