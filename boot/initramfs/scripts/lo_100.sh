#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py volset Lineout 100
sleep 1
echo "=== ZCD_CON1 after 100% ==="
grep -E "^228a:" "$R"
echo "=== CON4 ==="
grep -E "^2210:" "$R"
python3 alsa_test2.py hw:0,0 8 660 44100 s16
echo "=== during/after ==="
grep -E "^228a:|^2210:" "$R"
