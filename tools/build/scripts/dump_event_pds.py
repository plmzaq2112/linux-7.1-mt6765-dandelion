#!/usr/bin/env python3
import re
s = open('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/csbgen/rogue/cr.xml').read()
for name in ('EVENT_PIXEL_PDS_INFO',):
    i = s.index('<struct name="%s"' % name)
    j = s.index('</struct>', i)
    print('==', name)
    for m in re.finditer(r'<field name="([^"]+)" start="(\d+)" end="(\d+)"', s[i:j]):
        print(' ', m.group(1), m.group(2), m.group(3))
