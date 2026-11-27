#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py volset Lineout 100
python3 alsa_test2.py hw:0,0 10 440 44100 s16 > /tmp/spk7.log 2>&1 &
sleep 3
echo "=== regs during playback ==="
for a in 2208 220e 2210 2214 2220 2222 20b4 20b6 20b8 20ba 20bc 228a; do
    grep -E "^$a:" "$R"
done
sleep 8
cat /tmp/spk7.log
