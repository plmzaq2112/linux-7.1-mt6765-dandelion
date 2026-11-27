#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py volset Lineout 100
python3 alsa_test2.py hw:0,0 8 440 44100 s16 > /tmp/dump.log 2>&1 &
sleep 3
echo "=== all 0x22xx registers during speaker playback ==="
awk -F: '$1 >= "2200" && $1 <= "2290" {print}' "$R"
sleep 6
cat /tmp/dump.log
