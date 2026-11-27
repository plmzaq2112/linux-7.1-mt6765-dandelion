#include <stddef.h>
#include <stdio.h>
#include "fw-api/pvr_rogue_fwif.h"

#define P(st, f) printf("%-28s %4zu\n", #f, offsetof(struct st, f))
#define S(st) printf("sizeof(%s) = %zu\n", #st, sizeof(struct st))

int main(void)
{
   S(rogue_fwif_cmd_ta_3d_shared);
   S(rogue_fwif_ta_regs);
   S(rogue_fwif_3d_regs);
   S(rogue_fwif_cmd_ta);
   S(rogue_fwif_cmd_3d);
   S(rogue_fwif_cmd_transfer);
   puts("--- cmd_ta_3d_shared ---");
   P(rogue_fwif_cmd_ta_3d_shared, flags);
   P(rogue_fwif_cmd_ta_3d_shared, frame_num);
   P(rogue_fwif_cmd_ta_3d_shared, fence);
   puts("--- ta (offset in cmd) ---");
   P(rogue_fwif_cmd_ta, cmd_shared);
   P(rogue_fwif_cmd_ta, regs);
   P(rogue_fwif_cmd_ta, flags);
   P(rogue_fwif_cmd_ta, partial_render_ta_3d_fence);
   P(rogue_fwif_cmd_ta, dummy_rgnhdr_init_geom_regs);
   P(rogue_fwif_cmd_ta, brn61484_66333_live_rt);
   puts("--- 3d (offset in cmd) ---");
   P(rogue_fwif_cmd_3d, cmd_shared);
   P(rogue_fwif_cmd_3d, regs);
   P(rogue_fwif_cmd_3d, flags);
   P(rogue_fwif_cmd_3d, partial_render_ta_3d_fence);
   P(rogue_fwif_cmd_3d, brn61484_66333_live_rt);
   puts("--- 3d_regs ---");
   P(rogue_fwif_3d_regs, usc_pixel_output_ctrl);
   P(rogue_fwif_3d_regs, usc_clear_register);
   P(rogue_fwif_3d_regs, isp_bgobjdepth);
   P(rogue_fwif_3d_regs, isp_bgobjvals);
   P(rogue_fwif_3d_regs, isp_aa);
   P(rogue_fwif_3d_regs, isp_xtp_pipe_enable);
   P(rogue_fwif_3d_regs, isp_ctl);
   P(rogue_fwif_3d_regs, tpu);
   P(rogue_fwif_3d_regs, event_pixel_pds_info);
   P(rogue_fwif_3d_regs, pixel_phantom);
   P(rogue_fwif_3d_regs, view_idx);
   return 0;
}
