#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Headphone Left Source" 0
python3 mixer3.py enum "Headphone Right Source" 0
python3 mixer3.py volset Lineout 10

echo "=== gain ==="
python3 mixer3.py vols | grep -i '^Lineout'
grep -E '^228a:|^2210:|^2208:' "$R"

echo "=== 1kHz sine 8s ==="
timeout 8 python3 alsa_test2.py hw:0,0 8 1000 44100 s16
echo done
