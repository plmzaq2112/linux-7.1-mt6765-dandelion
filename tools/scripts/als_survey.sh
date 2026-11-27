#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
D=/tmp/vendor.dts
[ -f "$D" ] || dtc -I dtb -O dts -o "$D" /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/dist/phone.fdt 2>/dev/null

echo "=== vendor DTS: als / light / proximity ==="
grep -niE "als|light-sensor|lightsensor|proximity|psensor|stk3|ltr5|tcs3|epl2|cm36|rpr0521|ap3426|aw2|is31|opt3001" "$D" | head -30

echo
echo "=== vendor DTS: sensor 相关节点 ==="
grep -niE "hwmsen|sensor|sensors" "$D" | head -25

echo
echo "=== mainline dandelion DTS: sensor ==="
grep -rniE "als|light|proximity|accel|sensor|scp" "$T/arch/arm64/boot/dts/mediatek/" --include="*6765*" --include="*dandelion*" | head -25
