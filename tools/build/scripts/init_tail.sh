#!/bin/bash
cd /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/initrd21/root || exit 1
echo "=== init lines 80-200 ==="
sed -n '80,200p' init
