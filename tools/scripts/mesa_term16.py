#!/usr/bin/env python3
"""1.13: TA terminate clip granularity is 16 pixels, not 32"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_framebuffer.c')
s = p.read_text()

old = '''      term0.clip_right =
         DIV_ROUND_UP(
            width,
            ROGUE_TA_STATE_TERMINATE0_CLIP_RIGHT_BLOCK_SIZE_IN_PIXELS);
      term0.clip_bottom =
         DIV_ROUND_UP(
            height,
            ROGUE_TA_STATE_TERMINATE0_CLIP_BOTTOM_BLOCK_SIZE_IN_PIXELS);'''

new = '''      /* 1.13 firmware uses a 16 pixel terminate clip granularity. */
      term0.clip_right = DIV_ROUND_UP(width, 16) - 1;
      term0.clip_bottom = DIV_ROUND_UP(height, 16) - 1;'''

assert s.count(old) == 1, 'anchor not found'
s = s.replace(old, new, 1)
p.write_text(s)
print('terminate clip -> 16px units')
