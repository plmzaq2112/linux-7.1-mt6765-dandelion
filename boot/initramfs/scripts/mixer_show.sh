#!/bin/sh
cd /root/audio || exit 1
for n in "DAC Mux" "Headphone" "Headphone Left Source" "Headphone Right Source" "Handset Source" "DACL" "DACR"; do
    echo "== $n"
    python3 mixer2.py show "$n"
done
