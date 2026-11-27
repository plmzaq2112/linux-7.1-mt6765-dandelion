#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
D="$T/out/railmod2"
mkdir -p "$D"
cp "$W/kernel/modules/rail-en/rail_en2.c" "$D/rail_en2.c"
cat > "$D/Makefile" <<'EOF'
obj-m := rail_en2.o
EOF
make -C "$T" O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M="$D" modules 2>&1 | tail -6
cp "$D/rail_en2.ko" "$W/dist/rail_en2.ko"
ls -l "$W/dist/rail_en2.ko"
