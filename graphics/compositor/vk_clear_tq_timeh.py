#!/usr/bin/env python3
"""vk_clear_tq: add <time.h>"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_clear_tq.c')
s = p.read_text()

if '#include <time.h>' not in s:
    s = s.replace('#include <string.h>', '#include <string.h>\n#include <time.h>', 1)
    p.write_text(s)
    print('time.h added')
else:
    print('already there')
