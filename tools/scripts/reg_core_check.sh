#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== regulator_lookup_by_name exists? ==="
grep -n "regulator_lookup_by_name" "$T/drivers/regulator/core.c" | head
echo
echo "=== _regulator_get dev NULL handling ==="
sed -n '/static struct regulator \*_regulator_get/,/^}/p' "$T/drivers/regulator/core.c" | head -40
