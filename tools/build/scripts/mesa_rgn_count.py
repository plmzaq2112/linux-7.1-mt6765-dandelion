#!/usr/bin/env python3
"""1.13/GE8320: uiRgnHeaderSize is a header *count*, one per tile of the surface.

Mesa's non-simple path returns dwords for one macrotile group, and the winsys
hardcoded 16 (the tile count of a 64x64 surface), which caps the tiled area at
one 4x4-tile macrotile (64x64 px).
"""
from pathlib import Path

base = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr')

# 1. region size helper -> header count for GE8320
p = base / 'src/imagination/vulkan/pvr_arch_job_render.c'
s = p.read_text()

old = '''   const struct pvr_device_info *dev_info = &device->pdevice->dev_info;
   uint64_t rgn_size =
      (uint64_t)mtile_info->tiles_per_mtile_x * mtile_info->tiles_per_mtile_y;
'''

new = '''   const struct pvr_device_info *dev_info = &device->pdevice->dev_info;
   uint64_t rgn_size =
      (uint64_t)mtile_info->tiles_per_mtile_x * mtile_info->tiles_per_mtile_y;

   /* 1.13 GE8320 firmware wants a region header *count*, one per tile of the
    * whole surface (not the dword size of a single macrotile group).
    */
   if (dev_info->ident.b == 22 && dev_info->ident.v == 87 &&
       dev_info->ident.n == 104) {
      return (uint64_t)mtile_info->num_tiles_x * mtile_info->num_tiles_y;
   }
'''

assert s.count(old) == 1, 'anchor not found'
s = s.replace(old, new, 1)
p.write_text(s)
print('region header count patched')

# 2. winsys: stop overriding the value with 16
p = base / 'src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_render.c'
s = p.read_text()

old = '''   /* 1.13 GE8320 firmware expects uiRgnHeaderSize as a header count (16),
    * while Mesa computes it in dwords (20 with 5-byte headers).
    */
   uint32_t rgn_header_size = create_info->rgn_header_size;
   if (dev_info->ident.b == 22 && dev_info->ident.v == 87 &&
       dev_info->ident.n == 104)
      rgn_header_size = 16;
'''

new = '''   /* 1.13 GE8320 firmware expects uiRgnHeaderSize as a region header count;
    * pvr_rt_get_isp_region_size() already returns that for this device.
    */
   uint32_t rgn_header_size = create_info->rgn_header_size;
'''

assert s.count(old) == 1, 'winsys anchor not found'
s = s.replace(old, new, 1)
p.write_text(s)
print('winsys override removed')
