#!/usr/bin/env python3
"""env-gated probes for the 1.13 region-clip / terminate clip fields"""
from pathlib import Path

base = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr')

# framebuffer.c : terminate clip
p = base / 'src/imagination/vulkan/pvr_arch_framebuffer.c'
s = p.read_text()
if 'PVR13_TERM_R' not in s:
    old = '   pvr_csb_pack (&ppp_state[2], TA_STATE_TERMINATE1, term1) {'
    new = (
        '   {\n'
        '      const char *e;\n'
        '      if ((e = getenv("PVR13_TERM_R")))\n'
        '         term0.clip_right = (uint32_t)atoi(e);\n'
        '      if ((e = getenv("PVR13_TERM_B")))\n'
        '         term0.clip_bottom = (uint32_t)atoi(e);\n'
        '   }\n\n'
        + old
    )
    assert s.count(old) == 1, 'terminate anchor not found'
    s = s.replace(old, new, 1)
    if '#include <stdlib.h>' not in s:
        s = s.replace('#include "pvr_csb.h"', '#include <stdlib.h>\n\n#include "pvr_csb.h"', 1)
    p.write_text(s)
    print('framebuffer probe added')
else:
    print('framebuffer probe present')

# pvr_arch_cmd_buffer.c : region clip
p = base / 'src/imagination/vulkan/pvr_arch_cmd_buffer.c'
s = p.read_text()
if 'PVR13_RGN_R' not in s:
    old = '      /* Setup region clip to clip everything outside what was calculated. */'
    new = (
        '      {\n'
        '         const char *e;\n'
        '         if ((e = getenv("PVR13_RGN_R")))\n'
        '            right = (uint32_t)atoi(e);\n'
        '         if ((e = getenv("PVR13_RGN_B")))\n'
        '            bottom = (uint32_t)atoi(e);\n'
        '      }\n\n'
        + old
    )
    assert s.count(old) == 1, 'region clip anchor not found'
    s = s.replace(old, new, 1)
    p.write_text(s)
    print('region clip probe added')
else:
    print('region clip probe present')
