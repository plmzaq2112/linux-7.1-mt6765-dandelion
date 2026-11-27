#!/usr/bin/env python3
"""PVR13_DUMP_RT=1: print the RT dataset values Mesa hands to the kernel"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_render.c')
s = p.read_text()

if 'PVR13_DUMP_RT' in s:
    print('already present')
else:
    anchor = '''   result = pvr_srv_rgx_create_hwrt_dataset('''
    new = '''   if (getenv("PVR13_DUMP_RT")) {
      fprintf(stderr,
              "pvr-rt: %ux%u rgn=%llu isp_mtile=%08x te_screen=%08x "
              "mt1=%08x mt2=%08x stride=%u mtile_stride=%u tpc=%llu "
              "tpc_stride=%llu align=%u\\n",
              create_info->width, create_info->height,
              (unsigned long long)rgn_header_size, isp_mtile_size,
              rogue_te_regs.screen, rogue_te_regs.mtile1, rogue_te_regs.mtile2,
              rogue_te_regs.mtile_stride,
              create_info->tpc_stride,
              (unsigned long long)create_info->tpc_size,
              (unsigned long long)create_info->tpc_stride,
              create_info->samples);
   }

''' + anchor
    assert s.count(anchor) == 1, 'anchor not found'
    s = s.replace(anchor, new, 1)
    if '#include <stdio.h>' not in s:
        s = s.replace('#include <stdlib.h>', '#include <stdio.h>\n#include <stdlib.h>', 1)
    p.write_text(s)
    print('rt dump added')
