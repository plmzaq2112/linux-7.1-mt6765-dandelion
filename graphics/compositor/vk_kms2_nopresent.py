#!/usr/bin/env python3
"""vk_kms2: VK_KMS_NOPRESENT=1 to isolate render time from presentation"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_kms2.c')
s = p.read_text()

old = '''    int force_dumb = getenv("VK_KMS_DUMB") != NULL;'''
new = '''    int force_dumb = getenv("VK_KMS_DUMB") != NULL;
    int no_present = getenv("VK_KMS_NOPRESENT") != NULL;'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

old2 = '''        clock_gettime(CLOCK_MONOTONIC, &ts0);
        g_flip_done = 0;'''
new2 = '''        if (no_present) {
            frames++;
            cur ^= 1;
            continue;
        }

        clock_gettime(CLOCK_MONOTONIC, &ts0);
        g_flip_done = 0;'''
assert s.count(old2) == 1
s = s.replace(old2, new2, 1)

p.write_text(s)
print('nopresent added')
