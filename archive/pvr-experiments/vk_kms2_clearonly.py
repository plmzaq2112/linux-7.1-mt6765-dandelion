#!/usr/bin/env python3
"""vk_kms2: VK_KMS_CLEARONLY=1 skips the draws (measures the render-pass clear)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_kms2.c')
s = p.read_text()

old = '''    int draws_per_frame = getenv("VK_KMS_DRAWS") ? atoi(getenv("VK_KMS_DRAWS")) : 1;'''
new = '''    int draws_per_frame = getenv("VK_KMS_DRAWS") ? atoi(getenv("VK_KMS_DRAWS")) : 1;
    int clear_only = getenv("VK_KMS_CLEARONLY") != NULL;'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

old2 = '''        for (int d = 0; d < draws_per_frame; d++) {'''
new2 = '''        for (int d = 0; d < (clear_only ? 0 : draws_per_frame); d++) {'''
assert s.count(old2) == 1
s = s.replace(old2, new2, 1)

p.write_text(s)
print('clearonly added')
