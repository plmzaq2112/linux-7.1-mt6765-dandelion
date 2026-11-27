for d in /sys/bus/i2c/devices/5-*; do
	printf '%s: ' "$d"
	readlink "$d/driver" 2>/dev/null || echo "(no driver)"
done
