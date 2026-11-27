#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py volset Lineout 100
python3 alsa_test2.py hw:0,0 10 440 44100 s16 > /tmp/spk6.log 2>&1 &
sleep 3
echo "=== regs during playback ==="
grep -E "^2214:|^2210:|^228a:|^2216:" "$R"
sleep 8
cat /tmp/spk6.log
