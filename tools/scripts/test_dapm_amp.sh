#!/bin/sh
cd /root/audio || exit 1

python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Headphone Left Source" 0
python3 mixer3.py enum "Headphone Right Source" 0
python3 mixer3.py volset Lineout 25

echo "=== before play ==="
cat /sys/kernel/debug/gpio | grep spk-amp-en

timeout 15 python3 wav_play.py /root/audio/apex.wav &
pid=$!
sleep 3
echo "=== during play ==="
cat /sys/kernel/debug/gpio | grep spk-amp-en
wait $pid
sleep 1
echo "=== after play ==="
cat /sys/kernel/debug/gpio | grep spk-amp-en
