#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

# restore LO max (18 -> ZCD_CON1 0x0000)
python3 mixer3.py volset Lineout 100

# 2-in-1 test: speaker through headphone amp
python3 mixer3.py enum "Line Out Source" 0
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Headphone Left Source" 2
python3 mixer3.py enum "Headphone Right Source" 2
python3 mixer3.py volset Headphone 100

echo "=== mixers ==="
python3 mixer3.py vols
echo "=== zcd ==="
grep -E '^228a:|^2288:|^228c:' "$R"

echo "=== play 20s ==="
timeout 20 python3 wav_play.py /root/audio/apex.wav
echo "playback done"
