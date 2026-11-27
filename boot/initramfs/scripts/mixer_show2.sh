#!/bin/sh
cd /root/audio || exit 1
for n in "Handset" "Handset Source" "Lineout" "Line Out Source" "DAC Mux"; do
    echo "== $n"
    python3 mixer2.py show "$n"
    python3 mixer.py list >/dev/null 2>&1
done
