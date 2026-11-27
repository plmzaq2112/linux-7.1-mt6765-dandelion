#!/bin/sh
cd /root/audio || exit 1
python3 alsa_test.py hw:0,0 25 660 > /tmp/play.log 2>&1 &
PID=$!
i=0
while [ $i -lt 40 ]; do
    i=$((i + 1))
    st=$(grep '^state' /proc/asound/card0/pcm0p/sub0/status 2>/dev/null)
    case "$st" in
    *RUNNING*) break ;;
    esac
    sleep 0.5
done
echo "state after wait: $st (waited $i x0.5s)"
echo "=== irq/regs while running (t0) ==="
grep -E 'Afe_ISR' /proc/interrupts
cat /proc/asound/card0/pcm0p/sub0/status
python3 afe_reg.py read 0x3a0 0x3a4 0x3ac 0x3b4
sleep 2
echo "=== t+2s ==="
grep -E 'Afe_ISR' /proc/interrupts
cat /proc/asound/card0/pcm0p/sub0/status
python3 afe_reg.py read 0x3a0 0x3a4 0x3ac 0x3b4
sleep 2
echo "=== t+4s ==="
grep -E 'Afe_ISR' /proc/interrupts
cat /proc/asound/card0/pcm0p/sub0/status
python3 afe_reg.py read 0x3a0 0x3a4 0x3ac 0x3b4
kill $PID 2>/dev/null
