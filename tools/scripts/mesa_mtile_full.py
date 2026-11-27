#!/usr/bin/env python3
"""probe: PVR13_MTILE_FULL makes MTILE1/2 span the whole surface.

TE_MTILE1.x1 is documented as "left tile X for the second column of
macrotiles". Mesa writes ALIGN_POT(ceil(num_tiles/4), 4) there. If the 1.13
firmware instead reads it as "tiles per macrotile column", only the first
column is tiled, which would explain the 64x64 render cap on larger targets.
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_job_render.c')
s = p.read_text()

if 'PVR13_MTILE_FULL' not in s:
    old = '''      /* Set up 16 macrotiles with a multiple of 4x4 tiles per macrotile. */
      info->mtile_x1 = ALIGN_POT(DIV_ROUND_UP(info->num_tiles_x, 4), 4);
      info->mtile_y1 = ALIGN_POT(DIV_ROUND_UP(info->num_tiles_y, 4), 4);'''

    new = '''      /* Set up 16 macrotiles with a multiple of 4x4 tiles per macrotile. */
      if (getenv("PVR13_MTILE_FULL")) {
         info->mtile_x1 = ALIGN_POT(info->num_tiles_x, 4);
         info->mtile_y1 = ALIGN_POT(info->num_tiles_y, 4);
      } else {
         info->mtile_x1 = ALIGN_POT(DIV_ROUND_UP(info->num_tiles_x, 4), 4);
         info->mtile_y1 = ALIGN_POT(DIV_ROUND_UP(info->num_tiles_y, 4), 4);
      }'''

    assert s.count(old) == 1, 'anchor not found'
    s = s.replace(old, new, 1)
    if '#include <stdlib.h>' not in s:
        s = s.replace('#include "pvr_arch_job_render.h"',
                      '#include <stdlib.h>\n\n#include "pvr_arch_job_render.h"', 1)
    p.write_text(s)
    print('mtile full-width probe added')
else:
    print('probe present')
