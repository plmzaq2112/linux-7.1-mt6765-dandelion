#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

python3 mixer3.py enum "Line Out Source" 0
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Headphone Left Source" 2
python3 mixer3.py enum "Headphone Right Source" 2
python3 mixer3.py volset Headphone 0
python3 mixer3.py volset "Headphone Vin" 0
python3 alsa_test2.py hw:0,0 10 440 44100 s16 > /tmp/hp.log 2>&1 &
sleep 3
echo "=== regs during HP playback ==="
for a in 2208 2210 2214 228a 228c; do
    grep -E "^$a:" "$R"
done
sleep 8
cat /tmp/hp.log
