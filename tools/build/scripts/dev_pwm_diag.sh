#!/bin/sh
echo "=== pinmux 43 / 154 ==="
for d in /sys/kernel/debug/pinctrl/*/pinmux-pins; do
    grep -E "pin 43 |pin 154 " "$d" 2>/dev/null
done

echo
echo "=== gpio43 / gpio154 ==="
cat /sys/kernel/debug/gpio | grep -E "gpio-43 |gpio-154 "

echo
echo "=== pwm clocks ==="
grep -iE "pwm" /sys/kernel/debug/clk/clk_summary 2>/dev/null | head -6

echo
echo "=== pwm node dmesg ==="
dmesg | grep -iE "1100e000|pwm-mtk|mtk-disp-pwm" | tail -8

echo
echo "=== pwm regs now ==="
cat /sys/kernel/debug/pwm | sed -n '1,6p'
