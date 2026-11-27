echo "== kms-loop CPU =="
top -b -n 2 -d 1 2>/dev/null | grep -E 'kms-loop|Mem:' | tail -4
echo "== load =="
cat /proc/loadavg
echo "== cpu MHz/state =="
cat /proc/cpuinfo | grep -E 'BogoMIPS|Features' | head -2
