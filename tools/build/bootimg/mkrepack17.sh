#!/bin/bash
cd /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/scripts || exit 1
sed -e 's|boot-stable16-panelbl11-nodb.img|boot-stable17-panelbl2047.img|' \
    -e 's|/tmp/repack16|/tmp/repack17|' \
    repack_panelbl4.py > repack_panelbl5.py
grep -n "boot-stable1" repack_panelbl5.py
