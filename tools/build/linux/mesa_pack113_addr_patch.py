#!/usr/bin/env python3
"""Fix the 1.13 CMD3D address block.

Golden 64x64 clear:
  0x40 = 0x004dc000  <- event_pixel_pds_data, not scissor
  0x48 = 0x00d33000  <- isp_scissor_base
  0x50 = 0x00d3b000  <- isp_dbias_base
  0x58..0x70 = 0     <- oclqry/zlsctl/zload/sten
Our first packer shifted these one slot too early, so the EOT PDS program
never ran and the ISP stopped after ISP_END_MACROTILE.
"""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_render.c")
s = P.read_text(encoding="utf-8")

old = """   pvr_put_u64(dst + 0x40, r->isp_scissor_base);
   pvr_put_u64(dst + 0x48, r->isp_dbias_base);
   pvr_put_u64(dst + 0x50, r->isp_oclqry_base);
   pvr_put_u64(dst + 0x58, r->isp_zlsctl);
   pvr_put_u64(dst + 0x60, r->isp_zload_store_base);
   pvr_put_u64(dst + 0x68, r->isp_stencil_load_store_base);
   pvr_put_u64(dst + 0x70, r->fb_cdc_zls);
"""
new = """   pvr_put_u64(dst + 0x40, r->event_pixel_pds_data);
   pvr_put_u64(dst + 0x48, r->isp_scissor_base);
   pvr_put_u64(dst + 0x50, r->isp_dbias_base);
   pvr_put_u64(dst + 0x58, r->isp_oclqry_base);
   pvr_put_u64(dst + 0x60, r->isp_zlsctl);
   pvr_put_u64(dst + 0x68, r->isp_zload_store_base);
   pvr_put_u64(dst + 0x70, r->isp_stencil_load_store_base);
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched 3D address block")
