#!/bin/sh
for pair in "6 0x3e" "6 0x55" "3 0x57" "3 0x50" "3 0x34" "3 0x27" "2 0x20" "4 0x3f" "0 0x48" "1 0x48"; do
    set -- $pair
    echo "bus$1 addr$2 errno=$(python3 /root/audio/dev_probe_errno.py $1 $2)"
done
