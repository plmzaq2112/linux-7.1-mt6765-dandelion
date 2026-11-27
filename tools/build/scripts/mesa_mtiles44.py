#!/usr/bin/env python3
"""Revert the GE8320 'single 1x1 macrotile group' override.

It caps the tile/region capacity at 16 tiles (4x4 tiles of 16 px = 64x64 px),
which is why 128x128 and larger targets were clipped to 64x64 and why
720x1600 produced nothing at all.
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/include/hwdef/rogue_hw_utils.h')
s = p.read_text()

old = '''   /* 1.13 GE8320 (22.87.104.18) uses a single 1x1 macrotile group:
    * vendor tpc_size is 128 (4x4 tail pointers), not 2048.
    */
   if (dev_info->ident.b == 22 && dev_info->ident.v == 87 &&
       dev_info->ident.n == 104) {
      *x_out = 1;
      *y_out = 1;
   } else if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) ||
              version == 2) {'''

new = '''   if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) ||
       version == 2) {'''

assert s.count(old) == 1, 'anchor not found'
s = s.replace(old, new, 1)
p.write_text(s)
print('macrotile 4x4 restored')
