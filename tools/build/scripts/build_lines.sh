#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
D="$T/out/linesmod"
mkdir -p "$D"
cp "$W/tests/tools/i2c_lines.c" "$D/i2c_lines.c"
cat > "$D/Makefile" <<'EOF'
obj-m := i2c_lines.o
EOF
make -C "$T" O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M="$D" modules 2>&1 | tail -6
cp "$D/i2c_lines.ko" "$W/dist/i2c_lines.ko"
ls -l "$W/dist/i2c_lines.ko"
