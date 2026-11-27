#!/bin/sh
cd /root/audio || exit 1
R=/sys/kernel/debug/regmap/1000d000.pwrap/registers

echo "=== handset volume -> ZCD_CON3 (0x228e) ==="
grep -E "^228e:" "$R"
python3 mixer3.py volset Handset 100
sleep 1
grep -E "^228e:" "$R"

echo "=== lineout volume 50 -> ZCD_CON1 (0x228a) ==="
grep -E "^228a:" "$R"
python3 mixer3.py volset Lineout 50
sleep 1
grep -E "^228a:" "$R"

echo "=== dac mux / lineout source readback ==="
python3 mixer3.py show "Line Out Source" | tail -4
