#!/usr/bin/env python3
"""fix the terminate-clip probe: keep it inside the term0 packing block"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_framebuffer.c')
s = p.read_text()

start = s.index('   pvr_csb_pack (&ppp_state[1], TA_STATE_TERMINATE0, term0) {')
end = s.index('   pvr_csb_pack (&ppp_state[2], TA_STATE_TERMINATE1, term1) {')

new = '''   pvr_csb_pack (&ppp_state[1], TA_STATE_TERMINATE0, term0) {
      term0.clip_right =
         DIV_ROUND_UP(
            width,
            ROGUE_TA_STATE_TERMINATE0_CLIP_RIGHT_BLOCK_SIZE_IN_PIXELS);
      term0.clip_bottom =
         DIV_ROUND_UP(
            height,
            ROGUE_TA_STATE_TERMINATE0_CLIP_BOTTOM_BLOCK_SIZE_IN_PIXELS);

      /* 1.13 probe hooks. */
      {
         const char *e;

         if ((e = getenv("PVR13_TERM_R")))
            term0.clip_right = (uint32_t)atoi(e);
         if ((e = getenv("PVR13_TERM_B")))
            term0.clip_bottom = (uint32_t)atoi(e);
      }
   }

'''

s = s[:start] + new + s[end:]
p.write_text(s)
print('rewritten')
print(s[s.index('   pvr_csb_pack (&ppp_state[1]'):s.index('   pvr_csb_pack (&ppp_state[2]')])
