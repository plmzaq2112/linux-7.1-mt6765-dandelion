#!/usr/bin/env python3
"""1.13/GE8320: isp_bgobjdepth must be an IEEE float even for 16-bit int depth

Measured with vk_ds: D16 depth drew nothing with the UNORM16 clear value
(0xffff) and worked perfectly with fui(1.0f) = 0x3f800000
(colour red=3072 green=1024, depth centre 6553/65535 = 0.1).
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_job_render.c')
s = p.read_text()

old = '''      case ROGUE_CR_ZLS_FORMAT_TYPE_16BITINT:
         value.value = _mesa_float_to_unorm(depth_clear, 16);
         break;'''
new = '''      case ROGUE_CR_ZLS_FORMAT_TYPE_16BITINT:
         /* 1.13 GE8320 wants the background-object depth value as an IEEE
          * float even though the depth buffer is 16 bit integer; with the
          * UNORM16 encoding the ISP rejects every fragment.
          */
         if (device->pdevice->dev_info.ident.b == 22 &&
             device->pdevice->dev_info.ident.v == 87 &&
             device->pdevice->dev_info.ident.n == 104) {
            value.value = fui(depth_clear);
         } else {
            value.value = _mesa_float_to_unorm(depth_clear, 16);
         }
         break;'''
assert s.count(old) == 1, 'bgobjdepth anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('D16 bgobjdepth quirk applied')
