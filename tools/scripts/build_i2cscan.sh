#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
D="$T/out/i2cscanmod"
mkdir -p "$D"
cp "$W/tests/tools/i2cscan.c" "$D/i2cscan.c"
cat > "$D/Makefile" <<'EOF'
obj-m := i2cscan.o
EOF
make -C "$T" O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M="$D" modules 2>&1 | tail -6
cp "$D/i2cscan.ko" "$W/dist/i2cscan.ko"
ls -l "$W/dist/i2cscan.ko"
