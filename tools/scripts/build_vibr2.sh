#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
D="$T/out/vibmod"
mkdir -p "$D"
cp "$W/kernel/modules/regulator-vibrator/regulator-vibrator.c" "$D/regulator-vibrator.c"
cat > "$D/Makefile" <<'EOF'
obj-m := regulator-vibrator.o
EOF
make -C "$T" O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M="$D" modules 2>&1 | tail -40
