echo "== cpufreq =="
ls /sys/devices/system/cpu/cpu0/cpufreq 2>/dev/null | head -8
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null
echo "== power_supply =="
ls /sys/class/power_supply 2>/dev/null
for p in /sys/class/power_supply/*; do
	[ -d "$p" ] || continue
	printf '%s: ' "$p"
	cat "$p/type" 2>/dev/null | tr -d '\n'
	printf ' status='
	cat "$p/status" 2>/dev/null | tr -d '\n'
	printf ' cap='
	cat "$p/capacity" 2>/dev/null
done
echo "== thermal =="
ls /sys/class/thermal 2>/dev/null | head -5
echo "== mem =="
free | head -2
