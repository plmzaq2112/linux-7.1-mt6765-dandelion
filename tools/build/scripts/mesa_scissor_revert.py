#!/usr/bin/env python3
"""Revert the GE8320 scissor quirk: the ISP scissor table works (the earlier
'clips everything' symptom was the compositor's own Y-flip bug). Keep
PVR13_NOSCISSOR=1 as an opt-in disable for A/B tests."""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_cmd_buffer.c')
s = p.read_text()

old = '''      {
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
new = '''      /* The 1.13 ISP scissor table works. PVR13_NOSCISSOR=1 disables it and
       * leaves clipping to the (16 px granular) region clip, useful for A/B.
       */
      ispctl.scenable = !rasterizer_discard && !getenv("PVR13_NOSCISSOR");'''
assert s.count(old) == 1, 'scissor quirk anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('scissor quirk reverted')
