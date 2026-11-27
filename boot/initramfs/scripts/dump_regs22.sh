#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py volset Lineout 100
python3 alsa_test2.py hw:0,0 8 440 44100 s16 > /tmp/d.log 2>&1 &
sleep 3
for a in 2208 220a 220c 220e 2210 2212 2214 2216 2218 221a 221c 221e 2220 2222 2226 228a 228c 228e 20b4 20b6 20b8 20ba 20bc; do
    grep -E "^$a:" "$R"
done
sleep 6
cat /tmp/d.log
