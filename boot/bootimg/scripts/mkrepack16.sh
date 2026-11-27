#!/bin/bash
cd /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/scripts || exit 1
sed -e 's|boot-stable15-panelbl11.img|boot-stable16-panelbl11-nodb.img|' \
    -e 's|/tmp/repack15|/tmp/repack16|' \
    repack_panelbl3.py > repack_panelbl4.py
grep -n "boot-stable1" repack_panelbl4.py
