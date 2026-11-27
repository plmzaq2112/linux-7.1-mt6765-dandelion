#!/bin/sh
echo "=== pwm DT node ==="
for n in /proc/device-tree/soc/*pwm* /proc/device-tree/*pwm*; do
    [ -e "$n" ] || continue
    echo "-- $n"
    ls "$n"
done

echo
echo "=== pwm clocks property (hex, 32-bit BE cells) ==="
for n in /proc/device-tree/soc/*pwm*; do
    [ -e "$n/clocks" ] || continue
    od -An -tx4 "$n/clocks"
    cat "$n/clock-names" 2>/dev/null | tr -d '\0'; echo
done

echo
echo "=== clk_summary: pwm related, full ==="
grep -iE "pwm|disp_pwm|mm_ck|1100e000" /sys/kernel/debug/clk/clk_summary | head -20

echo
echo "=== pwm driver bound? ==="
ls -l /sys/bus/platform/drivers/mtk-disp-pwm/ 2>/dev/null
cat /sys/bus/platform/drivers/mtk-disp-pwm/1100e000.pwm/uevent 2>/dev/null
