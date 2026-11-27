killall kms-loop 2>/dev/null
sleep 1
cp /root/kms-loop /usr/local/bin/kms-loop
chmod +x /usr/local/bin/kms-loop
cp /root/anim.kmsa /root/anim.kmsa 2>/dev/null
nohup /usr/local/bin/kms-loop /dev/dri/card1 /root/anim.kmsa >/tmp/anim.log 2>&1 &
sleep 3
cat /tmp/anim.log
pid=$(pidof kms-loop)
echo "pid=$pid"
a=$(awk '{print $14+$15}' /proc/$pid/stat)
sleep 3
b=$(awk '{print $14+$15}' /proc/$pid/stat)
echo "ticks in 3s: $((b-a)) => ~$(( (b-a)*100/300 ))% of one core"
