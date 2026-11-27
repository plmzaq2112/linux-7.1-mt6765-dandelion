#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

# LO path, max gain, extamp already pulsed high by ampen.ko
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Headphone Left Source" 0
python3 mixer3.py enum "Headphone Right Source" 0
python3 mixer3.py volset Lineout 100

echo "=== state ==="
python3 mixer3.py vols
grep -E '^228a:|^2288:|^228c:' "$R"
echo "=== play 20s ==="
timeout 20 python3 wav_play.py /root/audio/apex.wav
echo done
