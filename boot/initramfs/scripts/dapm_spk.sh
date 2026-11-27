#!/bin/sh
cd /root/audio || exit 1
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py volset Lineout 100
python3 alsa_test2.py hw:0,0 8 660 44100 s16 > /tmp/spk.log 2>&1 &
sleep 2
D=/sys/kernel/debug/asoc/mt6765-evk/mt6357-sound/dapm
for w in "Line out" "Line Out Source" "DACL" "DAC Mux" "Handset Source"; do
    echo "== $w"
    cat "$D/$w" 2>/dev/null
done
sleep 7
cat /tmp/spk.log
