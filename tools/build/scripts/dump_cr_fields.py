#!/usr/bin/env python3
import re
p = "/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/csbgen/rogue/cr.xml"
s = open(p).read()
for name in ("TE_MTILE1", "TE_MTILE2", "TE_SCREEN", "ISP_MTILE_SIZE"):
    i = s.index('<struct name="%s"' % name)
    j = s.index("</struct>", i)
    block = s[i:j]
    print("==", name)
    for m in re.finditer(r'<field name="([^"]+)" start="(\d+)" end="(\d+)"', block):
        print("  ", m.group(1), m.group(2), m.group(3))
