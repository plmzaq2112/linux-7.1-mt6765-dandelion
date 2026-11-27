#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
L="$W/logs"
aarch64-linux-gnu-gcc -O2 -g0 -I /usr/include/libdrm \
    "$W/src/wayland/kms_prime_probe.c" -L /usr/lib/aarch64-linux-gnu -ldrm \
    -o "$L/kms_prime_probe"
ls -l "$L/kms_prime_probe"
