killall kms-loop 2>/dev/null
sleep 1
nohup /usr/local/bin/kms-loop /dev/dri/card1 /root/test-anim.kmsa >/tmp/anim.log 2>&1 &
sleep 3
pid=$(pidof kms-loop)
echo "pid=$pid"
if [ -n "$pid" ]; then
	a=$(awk '{print $14+$15}' /proc/$pid/stat)
	sleep 3
	b=$(awk '{print $14+$15}' /proc/$pid/stat)
	echo "ticks in 3s: $((b-a))  => ~$(( (b-a) * 100 / 300 ))% of one core"
fi
cat /tmp/anim.log
