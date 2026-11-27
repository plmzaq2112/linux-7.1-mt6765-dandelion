#!/usr/bin/env python3
"""3D probes for the D16 depth path: bgobjdepth / zlsctl / zls_stride"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_render.c')
s = p.read_text()

old = '''   {
      const char *e;
      if ((e = getenv("PVR13_ISPCTL")))
         pvr_put_u32(dst + 0x30, (uint32_t)strtoul(e, NULL, 0));
      if ((e = getenv("PVR13_BGobjVALS")))
         pvr_put_u32(dst + 0x28, (uint32_t)strtoul(e, NULL, 0));
      if (getenv("PVR13_3D_FLAGS0"))
         pvr_put_u32(dst + 0x130, 0);
   }'''
new = '''   {
      const char *e;
      if ((e = getenv("PVR13_ISPCTL")))
         pvr_put_u32(dst + 0x30, (uint32_t)strtoul(e, NULL, 0));
      if ((e = getenv("PVR13_BGobjVALS")))
         pvr_put_u32(dst + 0x28, (uint32_t)strtoul(e, NULL, 0));
      if (getenv("PVR13_3D_FLAGS0"))
         pvr_put_u32(dst + 0x130, 0);
      if ((e = getenv("PVR13_BGOBJDEPTH")))
         pvr_put_u32(dst + 0x24, (uint32_t)strtoul(e, NULL, 0));
      if ((e = getenv("PVR13_ZLSCTL")))
         pvr_put_u64(dst + 0x60, strtoull(e, NULL, 0));
      if ((e = getenv("PVR13_ZLSSTRIDE")))
         pvr_put_u32(dst + 0x134, (uint32_t)strtoul(e, NULL, 0));
      if ((e = getenv("PVR13_SLSSTRIDE")))
         pvr_put_u32(dst + 0x138, (uint32_t)strtoul(e, NULL, 0));
   }'''
assert s.count(old) == 1, 'probe block anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('depth probes added')
