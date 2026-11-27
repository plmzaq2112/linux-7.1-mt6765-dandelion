mount -t debugfs none /sys/kernel/debug 2>/dev/null
echo "== pinctrl dirs =="
ls /sys/kernel/debug/pinctrl/ 2>/dev/null
for d in /sys/kernel/debug/pinctrl/*/; do
	[ -d "$d" ] || continue
	echo "== $d"
	grep -E "pin (48|49) " "$d/pinmux-pins" 2>/dev/null | head -5
done
echo "== i2c clocks =="
grep -i i2c /sys/kernel/debug/clk/clk_summary 2>/dev/null | head -8
