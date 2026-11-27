#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
aarch64-linux-gnu-gcc -O2 -g0 -shared -fPIC \
    "$W/scripts/pvr_dump_shim.c" -o "$W/logs/libpvr_dump.so" -ldl
ls -l "$W/logs/libpvr_dump.so"
