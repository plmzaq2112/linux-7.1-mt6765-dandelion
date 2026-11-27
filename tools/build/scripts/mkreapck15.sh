#!/bin/bash
cd /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/scripts || exit 1
sed -e 's|boot-stable14-panelbl2.img|boot-stable15-panelbl11.img|' \
    -e 's|/tmp/repack14|/tmp/repack15|' \
    repack_panelbl2.py > repack_panelbl3.py
grep -n "boot-stable1" repack_panelbl3.py
