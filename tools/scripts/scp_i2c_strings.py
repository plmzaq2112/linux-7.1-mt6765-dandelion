#!/usr/bin/env python3
import re

raw = open("/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/scp2.bin", "rb").read()
strs = re.findall(rb"[\x20-\x7e]{4,}", raw)
seen = set()
for s in strs:
    t = s.decode("ascii", "ignore")
    low = t.lower()
    if ("i2c" in low or "als" in low or "ps_" in low or "sc7a" in low or "stk" in low) and t not in seen:
        seen.add(t)
        print(t[:120])
