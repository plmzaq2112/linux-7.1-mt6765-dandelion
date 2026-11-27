#!/usr/bin/env python3
"""1.13/GE8320 tiling model = one single macrotile covering the whole surface.

Vendor golden (720x1600, 16 px tiles -> 45x100 tiles), captured with
pvr_dump_hwrt:
  te_screen=0006302c  (xmax=44, ymax=99)
  mt1=00b40000        (x1=45, x2=0, x3=0)
  mt2=01900000        (y1=100, y2=0, y3=0)
  stride=00001194     (ui32MTileStride = 4500 = 45*100)
  rgn=1194            (region header count = 4500)
  isp_mtile=002d0064  (x=45, y=100)
  tpc=131072/0

So mtile_x1/y1 are the *whole* tile count, x2/x3 stay zero, and there is a
single 1x1 macrotile group.
"""
from pathlib import Path

base = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr')

# 1. single 1x1 macrotile group again
p = base / 'src/imagination/include/hwdef/rogue_hw_utils.h'
s = p.read_text()
old = '''   if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) ||
       version == 2) {'''
new = '''   /* 1.13 GE8320 (22.87.104.18) tiles the whole surface as one macrotile.
    * Vendor golden (720x1600): mt1 x1=45, mt2 y1=100, stride=4500.
    */
   if (dev_info->ident.b == 22 && dev_info->ident.v == 87 &&
       dev_info->ident.n == 104) {
      *x_out = 1;
      *y_out = 1;
   } else if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) ||
              version == 2) {'''
assert s.count(old) == 1, 'hw_utils anchor'
s = s.replace(old, new, 1)
p.write_text(s)
print('1x1 macrotile group restored')

# 2. mtile_x1/y1 = full tile count for GE8320
p = base / 'src/imagination/vulkan/pvr_arch_job_render.c'
s = p.read_text()
old = '''   if (PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format)) {'''
new = '''   if (dev_info->ident.b == 22 && dev_info->ident.v == 87 &&
       dev_info->ident.n == 104) {
      /* 1.13 GE8320: one macrotile spanning the whole render target.
       * Vendor golden (720x1600, 45x100 tiles): MTILE1.x1 = 45,
       * MTILE2.y1 = 100, x2/x3 = y2/y3 = 0, MTileStride = 4500.
       */
      info->mtile_x1 = info->num_tiles_x;
      info->mtile_y1 = info->num_tiles_y;
      info->mtile_x2 = 0;
      info->mtile_y2 = 0;
      info->mtile_x3 = 0;
      info->mtile_y3 = 0;
      info->x_tile_max = info->num_tiles_x - 1;
      info->y_tile_max = info->num_tiles_y - 1;
   } else if (PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format)) {'''
assert s.count(old) == 1, 'mtile_info anchor'
s = s.replace(old, new, 1)
p.write_text(s)
print('GE8320 single full-surface macrotile patched')
