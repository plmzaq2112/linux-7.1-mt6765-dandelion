#!/usr/bin/env python3
import re
s = open('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/csbgen/rogue/cr.xml').read()
for name in ('ISP_SCISSOR_BASE', 'ISP_DBIAS_BASE', 'ISP_OCLQRY_BASE'):
    i = s.index('<struct name="%s"' % name)
    j = s.index('</struct>', i)
    print('==', name)
    block = s[i:j]
    for m in re.finditer(r'<field name="([^"]+)" start="(\d+)" end="(\d+)"([^>]*)>', block):
        print(' ', m.group(1), m.group(2), m.group(3), m.group(4).strip())
