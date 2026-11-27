#!/usr/bin/env python3
"""Try the vendor golden ISP_CTL (tile grouping) instead of Mesa's computed
value.  The first successful clear only covered 32x16 (one tile group), which
points at the isp_ctl tile-in-flight configuration."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_render.c")
s = P.read_text(encoding="utf-8")

old = "   pvr_put_u32(dst + 0x30, r->isp_ctl);\n"
new = ("   /* Vendor GLES golden for 64x64: 0x3600f.  Mesa's computed value\n"
       "    * (0x33000) only produced one 32x16 tile group.\n"
       "    */\n"
       "   pvr_put_u32(dst + 0x30, 0x3600f);\n")
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched isp_ctl")
