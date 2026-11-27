#!/bin/sh
cd /root/audio || exit 1
echo "=== irq before ==="
grep -E 'Afe_ISR|mt_cmdq' /proc/interrupts
python3 alsa_test.py hw:0,0 30 660 > /tmp/play.log 2>&1 &
PID=$!
sleep 3
echo "=== t=3s ==="
grep -E 'Afe_ISR' /proc/interrupts
cat /proc/asound/card0/pcm0p/sub0/status
python3 afe_reg.py read 0x3a0 0x3a4 0x3b4
sleep 3
echo "=== t=6s ==="
grep -E 'Afe_ISR' /proc/interrupts
cat /proc/asound/card0/pcm0p/sub0/status
python3 afe_reg.py read 0x3a0 0x3a4 0x3b4
sleep 3
echo "=== t=9s ==="
grep -E 'Afe_ISR' /proc/interrupts
cat /proc/asound/card0/pcm0p/sub0/status
kill $PID 2>/dev/null
sleep 1
echo "=== play log ==="
cat /tmp/play.log
