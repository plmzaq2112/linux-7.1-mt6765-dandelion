#!/bin/sh
cd /root/audio || exit 1
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py volset Lineout 100
python3 alsa_test2.py hw:0,0 10 660 44100 s16 > /tmp/spk.log 2>&1 &
sleep 3
echo "=== codec regs during playback ==="
for r in 2208 220a 220c 220e 2210 2214 221c 221e 2220 2222 228a 20b4 20b6 20b8 20ba 20bc; do
    grep -E "^$r:" /sys/kernel/debug/regmap/1000d000.pwrap/registers
done
echo "=== DAPM ==="
D=/sys/kernel/debug/asoc/mt6765-evk/mt6357-sound/dapm
cat "$D/Line out" 2>/dev/null | head -1
sleep 8
cat /tmp/spk.log
