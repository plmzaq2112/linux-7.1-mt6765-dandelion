#!/usr/bin/env python3
"""GE8320: default to region-clip-only clipping (ISP scissor table is broken)

The 1.13 ISP scissor table makes the ISP clip everything away; the region clip
(derived from viewport^scissor, 16 px granularity) works. Default the quirk on
for this core; PVR13_SCISSOR=1 restores the upstream behaviour.
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_cmd_buffer.c')
s = p.read_text()

old = '''      ispctl.scenable = !rasterizer_discard && !getenv("PVR13_NOSCISSOR");'''
new = '''      {
         const struct pvr_device_info *di =
            &cmd_buffer->device->pdevice->dev_info;
         const bool ge8320_113 =
            di->ident.b == 22 && di->ident.v == 87 && di->ident.n == 104;

         /* 1.13 GE8320: the ISP scissor table (isp_scissor_base +
          * STATE_ISPDBSC.scindex) makes the ISP clip everything away, so rely
          * on the region clip (viewport^scissor, 16 px granularity) instead.
          * PVR13_SCISSOR=1 restores the upstream behaviour.
          */
         ispctl.scenable = !rasterizer_discard &&
                           !(ge8320_113 && !getenv("PVR13_SCISSOR"));
      }'''
assert s.count(old) == 1, 'scenable anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('GE8320 scissor quirk baked in')
