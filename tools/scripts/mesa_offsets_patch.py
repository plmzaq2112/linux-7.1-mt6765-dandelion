#!/usr/bin/env python3
"""Print exact struct offsets once, gated by PVR_DUMP_CMD."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv_bridge.c")
s = P.read_text(encoding="utf-8")

if "pvr_offsets_once" not in s:
    old = '#include "fw-api/pvr_rogue_fwif_shared.h"\n'
    new = '#include "fw-api/pvr_rogue_fwif.h"\n#include "fw-api/pvr_rogue_fwif_shared.h"\n'
    assert s.count(old) == 1
    s = s.replace(old, new, 1)

    old = "static void pvr_dump_cmd(const char *tag, const void *data, uint32_t size)\n"
    new = """static void pvr_offsets_once(void)
{
   static bool done;

   if (done)
      return;
   done = true;

   fprintf(stderr,
           "pvr-off cmd3d=%zu shared=%zu regs=%zu flags=%zu ufo=%zu brn=%zu\\n",
           sizeof(struct rogue_fwif_cmd_3d),
           offsetof(struct rogue_fwif_cmd_3d, cmd_shared),
           offsetof(struct rogue_fwif_cmd_3d, regs),
           offsetof(struct rogue_fwif_cmd_3d, flags),
           offsetof(struct rogue_fwif_cmd_3d, partial_render_ta_3d_fence),
           offsetof(struct rogue_fwif_cmd_3d, brn61484_66333_live_rt));
   fprintf(stderr,
           "pvr-off 3dregs=%zu usc_out=%zu usc_clear=%zu bgdepth=%zu bgvals=%zu "
           "aa=%zu xtp=%zu ctl=%zu tpu=%zu pdsinfo=%zu phantom=%zu view=%zu\\n",
           sizeof(struct rogue_fwif_3d_regs),
           offsetof(struct rogue_fwif_3d_regs, usc_pixel_output_ctrl),
           offsetof(struct rogue_fwif_3d_regs, usc_clear_register),
           offsetof(struct rogue_fwif_3d_regs, isp_bgobjdepth),
           offsetof(struct rogue_fwif_3d_regs, isp_bgobjvals),
           offsetof(struct rogue_fwif_3d_regs, isp_aa),
           offsetof(struct rogue_fwif_3d_regs, isp_xtp_pipe_enable),
           offsetof(struct rogue_fwif_3d_regs, isp_ctl),
           offsetof(struct rogue_fwif_3d_regs, tpu),
           offsetof(struct rogue_fwif_3d_regs, event_pixel_pds_info),
           offsetof(struct rogue_fwif_3d_regs, pixel_phantom),
           offsetof(struct rogue_fwif_3d_regs, view_idx));
   fprintf(stderr, "pvr-off cmdta=%zu taregs=%zu taflags=%zu\\n",
           sizeof(struct rogue_fwif_cmd_ta),
           offsetof(struct rogue_fwif_cmd_ta, regs),
           offsetof(struct rogue_fwif_cmd_ta, flags));
   fprintf(stderr, "pvr-off cmdtr=%zu trregs=%zu\\n",
           sizeof(struct rogue_fwif_cmd_transfer),
           offsetof(struct rogue_fwif_cmd_transfer, sTransRegs));
}

static void pvr_dump_cmd(const char *tag, const void *data, uint32_t size)
"""
    assert s.count(old) == 1
    s = s.replace(old, new, 1)

    old = "   if (!data || !size || !pvr_dump_cmd_enabled())\n      return;\n"
    new = "   if (!data || !size || !pvr_dump_cmd_enabled())\n      return;\n\n   pvr_offsets_once();\n"
    assert s.count(old) == 1
    s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched offsets print")
