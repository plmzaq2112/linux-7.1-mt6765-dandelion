#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
C="$T/drivers/power/supply"

echo "=== bq256xx config ==="
grep -n "BQ256XX" "$T/out/.config"

echo
echo "=== bq256xx regs ==="
ls "$C" | grep -i bq256
grep -rn "OTG_CONFIG\|CHARGER_CONTROL\|BOOST_LIM\|OTG" "$C"/bq256xx*.h "$C"/bq256xx*.c 2>/dev/null | head -25

echo
echo "=== regulator support in driver? ==="
grep -n "regulator\|REGULATOR" "$C/bq256xx_charger.c" | head
