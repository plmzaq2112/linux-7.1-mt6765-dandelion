#!/bin/bash
cd "$HOME/AI Project/Redmi 9A/kernel 7.1 mainline" || exit 1
DTC=scripts/dtc/dtc
[ -x "$DTC" ] || DTC=dtc
echo "using: $DTC"
"$DTC" -I dtb -O dts -o /tmp/r96.dts r96-dandelion.dtb 2>/dev/null || { echo "dtc failed"; exit 1; }

echo "=== mmc0 (eMMC) node ==="
awk '/mmc@11230000 \{/,/^\t\};/' /tmp/r96.dts | head -40
echo "=== mmc1 (SD) node ==="
awk '/mmc@11240000 \{/,/^\t\};/' /tmp/r96.dts | head -30
echo "=== mmc0 pins: DAT pad functions ==="
grep -n 'MSDC0_DAT[0-9]\|MSDC0_CMD\|MSDC0_CLK\|MSDC0_DS' /tmp/r96.dts | head -20
echo "=== hs400 props anywhere ==="
grep -n 'hs400\|hs200\|mmc-ddr' /tmp/r96.dts | head -20
