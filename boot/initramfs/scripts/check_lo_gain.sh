#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

echo "=== before ==="
grep -E "^228a:" "$R"

python3 mixer3.py volset Lineout 100
sleep 1
echo "=== after volset Lineout 100 ==="
grep -E "^228a:" "$R"

python3 mixer3.py vols | grep -i lineout

python3 mixer3.py enum "Line Out Source" 2
sleep 1
echo "=== after mux=Playback ==="
grep -E "^228a:" "$R"

python3 alsa_test2.py hw:0,0 5 660 44100 s16 > /tmp/spk.log 2>&1 &
sleep 2
echo "=== during playback ==="
grep -E "^228a:" "$R"
sleep 5
cat /tmp/spk.log
