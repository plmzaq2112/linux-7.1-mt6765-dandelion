#!/usr/bin/env python3
"""PVR13_RGN_STRIDE: override CR_TE_PSG.region_stride"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_job_render.c')
s = p.read_text()

old = '''      value.region_stride = rt_dataset->rgn_headers_stride /
                            ROGUE_CR_TE_PSG_REGION_STRIDE_UNIT_SIZE;'''
new = '''      value.region_stride = rt_dataset->rgn_headers_stride /
                            ROGUE_CR_TE_PSG_REGION_STRIDE_UNIT_SIZE;
      {
         const char *e = getenv("PVR13_RGN_STRIDE");

         if (e)
            value.region_stride = (uint32_t)strtoul(e, NULL, 0);
      }'''
assert s.count(old) == 1, 'region_stride anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('region_stride probe added')
