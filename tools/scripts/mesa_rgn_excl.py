#!/usr/bin/env python3
"""PVR13_RGN_EXCL=1: region clip right/bottom without the -1 (exclusive edge)"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_cmd_buffer.c')
s = p.read_text()

old = '''      if ((x + width) != 0U)
         right = DIV_ROUND_UP(x + width, region_clip_align_size) - 1;
      else
         right = 0;

      if ((y + height) != 0U)
         bottom = DIV_ROUND_UP(y + height, region_clip_align_size) - 1;
      else
         bottom = 0U;'''
new = '''      if ((x + width) != 0U)
         right = DIV_ROUND_UP(x + width, region_clip_align_size) -
                 (getenv("PVR13_RGN_EXCL") ? 0U : 1U);
      else
         right = 0;

      if ((y + height) != 0U)
         bottom = DIV_ROUND_UP(y + height, region_clip_align_size) -
                  (getenv("PVR13_RGN_EXCL") ? 0U : 1U);
      else
         bottom = 0U;'''
assert s.count(old) == 1, 'region clip anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('PVR13_RGN_EXCL probe added')
