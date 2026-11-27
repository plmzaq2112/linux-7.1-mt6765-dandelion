echo "== nodes with backlight/bled/lcd in name =="
find /proc/device-tree -iname '*backlight*' -o -iname '*bled*' -o -iname '*lcd*' 2>/dev/null | head -20
echo "== compatibles containing backlight/led/pwm =="
for f in $(find /proc/device-tree -name compatible 2>/dev/null); do
	c=$(tr -d '\0' < "$f" 2>/dev/null)
	case "$c" in
		*backlight*|*bled*|*pwm*|*led*) printf '%s: %s\n' "$f" "$c";;
	esac
done | head -30
echo "== mt6370 pmic status =="
tr -d '\0' < /proc/device-tree/soc/i2c@11016000/pmic@34/status 2>/dev/null; echo
