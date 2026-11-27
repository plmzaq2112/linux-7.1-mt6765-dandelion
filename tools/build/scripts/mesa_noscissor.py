#!/usr/bin/env python3
"""PVR13_NOSCISSOR=1: keep ISP scissor disabled, rely on the region clip only

The 1.13 ISP scissor table (isp_scissor_base + STATE_ISPDBSC.scindex) appears to
make the ISP clip everything away; the region clip alone is correct (verified in
the decoded PPP state), so test using it as the sole clipper.
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_cmd_buffer.c')
s = p.read_text()

old = '''      ispctl.scenable = !rasterizer_discard;'''
new = '''      ispctl.scenable = !rasterizer_discard && !getenv("PVR13_NOSCISSOR");'''
assert s.count(old) == 1, 'scenable anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('PVR13_NOSCISSOR probe added')
