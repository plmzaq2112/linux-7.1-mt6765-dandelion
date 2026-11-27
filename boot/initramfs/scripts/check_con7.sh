#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

echo "=== lineout playback: CON7 (0x2216) ==="
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py volset Lineout 100
python3 alsa_test2.py hw:0,0 6 440 44100 s16 > /tmp/s1.log 2>&1 &
sleep 2
grep -E "^2216:" "$R"
sleep 5

echo "=== handset playback: CON7 ==="
python3 mixer3.py enum "Line Out Source" 0
python3 mixer3.py enum "Handset Source" 2
python3 mixer3.py volset Handset 0
python3 alsa_test2.py hw:0,0 6 440 44100 s16 > /tmp/s2.log 2>&1 &
sleep 2
grep -E "^2216:" "$R"
sleep 5
cat /tmp/s1.log /tmp/s2.log
