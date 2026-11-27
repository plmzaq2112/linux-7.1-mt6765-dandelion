#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"

echo "=== vendor mt6370 reset/pascode ==="
sed -n '140,200p' "$V/drivers/misc/mediatek/pmic/mt6370/mt6370_pmu_core.c"
echo
echo "=== vendor pascode regs ==="
grep -rn "RSTPASCODE\|PASCODE" "$V/drivers/misc/mediatek/pmic/mt6370/inc/" | head -10
echo
echo "=== mainline mt6370 regs ==="
grep -rn "DEV_INFO\|PASCODE\|RSTPAS" "$T/drivers/mfd/mt6370.h" "$T/include/linux/mfd/mt6370.h" 2>/dev/null | head -15
