#!/bin/bash
F=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/stk3338.txt
echo "=== slave address / chip id ==="
grep -niE "slave address|i2c address|0x47|chip id|part id|device id" "$F" | head -20
echo
echo "=== register map lines ==="
grep -niE "REG_|register name|addr" "$F" | head -40
