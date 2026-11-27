#!/usr/bin/env python3
"""GE8320: write TE_MTILE1/2 x2,x3,y2,y3 as well.

The earlier 'only write x1/y1' came from a vendor 64x64 test, where a single
macrotile column is correct (x2=x3=0). Leaving them 0 on larger screens makes
all macrotile columns overlap the first one, so only one macrotile (64x64 px
with 16 px tiles) is ever tiled/rendered.
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_render.c')
s = p.read_text()

old1 = '''      if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) &&
          !PVR_DEVICE_IS_GE8320_113(dev_info)) {
         value.x2 = mtile_info->mtile_x2;
         value.x3 = mtile_info->mtile_x3;
      }'''
new1 = '''      if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format)) {
         value.x2 = mtile_info->mtile_x2;
         value.x3 = mtile_info->mtile_x3;
      }'''

old2 = '''      if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) &&
          !PVR_DEVICE_IS_GE8320_113(dev_info)) {
         value.y2 = mtile_info->mtile_y2;
         value.y3 = mtile_info->mtile_y3;
      }'''
new2 = '''      if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format)) {
         value.y2 = mtile_info->mtile_y2;
         value.y3 = mtile_info->mtile_y3;
      }'''

assert s.count(old1) == 1 and s.count(old2) == 1, 'anchors not found'
s = s.replace(old1, new1, 1).replace(old2, new2, 1)
p.write_text(s)
print('mtile x2/x3 y2/y3 enabled for GE8320')
