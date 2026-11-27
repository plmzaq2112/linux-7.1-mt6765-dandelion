#!/bin/bash
cd /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/initrd21 || exit 1
rm -rf root && mkdir -p root
cd root || exit 1
cpio -idm --no-absolute-filenames < ../initrd.cpio 2>/dev/null
echo "=== /init ==="
cat init 2>/dev/null | head -80
