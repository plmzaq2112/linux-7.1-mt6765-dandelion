#!/usr/bin/env python3
"""GE8320: single macrotile spanning the whole surface (see mesa golden dump).

Also drops the PVR13_MTILE_FULL probe, no longer needed.
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_job_render.c')
s = p.read_text()

old = '''   rogue_get_num_macrotiles_xy(dev_info, &info->mtiles_x, &info->mtiles_y);

   if (PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format)) {'''

new = '''   rogue_get_num_macrotiles_xy(dev_info, &info->mtiles_x, &info->mtiles_y);

   if (dev_info->ident.b == 22 && dev_info->ident.v == 87 &&
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

assert s.count(old) == 1, 'anchor'
s = s.replace(old, new, 1)

old2 = '''      /* Set up 16 macrotiles with a multiple of 4x4 tiles per macrotile. */
      if (getenv("PVR13_MTILE_FULL")) {
         info->mtile_x1 = ALIGN_POT(info->num_tiles_x, 4);
         info->mtile_y1 = ALIGN_POT(info->num_tiles_y, 4);
      } else {
         info->mtile_x1 = ALIGN_POT(DIV_ROUND_UP(info->num_tiles_x, 4), 4);
         info->mtile_y1 = ALIGN_POT(DIV_ROUND_UP(info->num_tiles_y, 4), 4);
      }'''

new2 = '''      /* Set up 16 macrotiles with a multiple of 4x4 tiles per macrotile. */
      info->mtile_x1 = ALIGN_POT(DIV_ROUND_UP(info->num_tiles_x, 4), 4);
      info->mtile_y1 = ALIGN_POT(DIV_ROUND_UP(info->num_tiles_y, 4), 4);'''

assert s.count(old2) == 1, 'mtile_full probe anchor'
s = s.replace(old2, new2, 1)

p.write_text(s)
print('GE8320 single full-surface macrotile patched')
