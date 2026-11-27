#!/usr/bin/env python3
"""vk_comp: fix the layer Y mapping (Vulkan NDC +Y points down)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

old = '''        float y0 = 1.0f - l->y / (float)h * 2.0f;
        float y1 = 1.0f - (l->y + l->h) / (float)h * 2.0f;'''
new = '''        /* Vulkan clip space: y = +1 is the *bottom* of the framebuffer. */
        float y0 = l->y / (float)h * 2.0f - 1.0f;
        float y1 = (l->y + l->h) / (float)h * 2.0f - 1.0f;'''
assert s.count(old) == 1, 'y mapping'
s = s.replace(old, new, 1)

p.write_text(s)
print('layer Y mapping fixed')
