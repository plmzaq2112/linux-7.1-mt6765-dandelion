#!/usr/bin/env python3
"""mesa: always align the region-header stride to 512 bits

pvr_rt_get_region_headers_stride_size() only aligned the per-RT region header
stride when simple_internal_parameter_format is present, so on this 1.13 core
RT data 1 got a region header base of va+22500 (0x57e4, 36 byte offset) while
TE_PSGREGION_ADDR requires 512-bit alignment.

Also: region_stride in CR_TE_PSG must round up (22500 B = 6 pages, not 5).
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_job_render.c')
s = p.read_text()

old = '''   if (PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format)) {
      rgn_headers_size =
         ALIGN_POT(rgn_headers_size, ROGUE_CR_TE_PSGREGION_ADDR_BASE_ALIGNMENT);
   }
'''
new = '''   /* Region headers must always be 512-bit aligned, not only for cores with
    * the simple internal parameter format.
    */
   rgn_headers_size =
      ALIGN_POT(rgn_headers_size, ROGUE_CR_TE_PSGREGION_ADDR_BASE_ALIGNMENT);
'''
assert s.count(old) == 1, 'align anchor'
s = s.replace(old, new, 1)

old2 = '''      value.region_stride = rt_dataset->rgn_headers_stride /
                            ROGUE_CR_TE_PSG_REGION_STRIDE_UNIT_SIZE;'''
new2 = '''      value.region_stride =
         DIV_ROUND_UP(rt_dataset->rgn_headers_stride,
                      ROGUE_CR_TE_PSG_REGION_STRIDE_UNIT_SIZE);'''
assert s.count(old2) == 1, 'region_stride anchor'
s = s.replace(old2, new2, 1)

p.write_text(s)
print('region header alignment + region_stride ceil applied')
