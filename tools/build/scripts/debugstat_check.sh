#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== DEBUGSTAT defines ==="
grep -nE "DEBUGSTAT|DEBUGCTRL|OFFSET_DEBUG" "$T/drivers/i2c/busses/i2c-mt65xx.c" | head -10
echo
echo "=== strict devmem config ==="
grep -nE "CONFIG_STRICT_DEVMEM|CONFIG_IO_STRICT_DEVMEM" "$T/out/.config"
