#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
aarch64-linux-gnu-gcc -O2 -g0 "$W/scripts/gles_clear.c" -o "$W/logs/gles_clear" -ldl
ls -l "$W/logs/gles_clear"
