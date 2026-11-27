#!/usr/bin/env python3
"""3D stream probes: PVR13_ISPCTL / PVR13_BGobjVALS / PVR13_3D_FLAGS0"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_render.c')
s = p.read_text()

old = '''   pvr_put_u32(dst + 0x130, src->flags);'''
new = '''   pvr_put_u32(dst + 0x130, src->flags);

   {
      const char *e;
      if ((e = getenv("PVR13_ISPCTL")))
         pvr_put_u32(dst + 0x30, (uint32_t)strtoul(e, NULL, 0));
      if ((e = getenv("PVR13_BGobjVALS")))
         pvr_put_u32(dst + 0x28, (uint32_t)strtoul(e, NULL, 0));
      if (getenv("PVR13_3D_FLAGS0"))
         pvr_put_u32(dst + 0x130, 0);
   }'''
assert s.count(old) == 1, 'flags anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('3d probes added')
