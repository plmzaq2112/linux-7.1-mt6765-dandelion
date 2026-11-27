pid=$(pidof kms-loop)
echo "pid=$pid"
if [ -n "$pid" ]; then
	a=$(awk '{print $14+$15}' /proc/$pid/stat)
	sleep 2
	b=$(awk '{print $14+$15}' /proc/$pid/stat)
	echo "cpu ticks in 2s: $((b-a)) (HZ=100 -> $(( (b-a) * 100 / 200 ))% of one core)"
fi
echo "== per-cpu idle sample =="
grep -E '^cpu[0-7] ' /proc/stat
sleep 1
grep -E '^cpu[0-7] ' /proc/stat
