#!/usr/bin/env python3
"""Print named TA/3D command fields when dumping, for golden comparison."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv_bridge.c")
s = P.read_text(encoding="utf-8")

if "pvr-ta " not in s:
    old = """   for (uint32_t off = 0; off < size; off += 16) {
      fprintf(stderr, "pvr-cmd-%s %04x:", tag, off);"""
    new = """   if (!strcmp(tag, "TA") && size >= sizeof(struct rogue_fwif_cmd_ta)) {
      const struct rogue_fwif_cmd_ta *c = data;
      const struct rogue_fwif_ta_regs *r = &c->regs;

      fprintf(stderr,
              "pvr-ta vdm=%llx tpub=%llx ppp=%08x te_psg=%08x tpu=%08x "
              "resume0=%08x resume3=%08x pds_ctrl=%08x view=%08x coeff=%08x "
              "flags=%08x fence=%llx:%08x\\n",
              (unsigned long long)r->vdm_ctrl_stream_base,
              (unsigned long long)r->tpu_border_colour_table,
              r->ppp_ctrl, r->te_psg, r->tpu,
              r->vdm_context_resume_task0_size,
              r->vdm_context_resume_task3_size,
              r->pds_ctrl, r->view_idx, r->pds_coeff_free_prog,
              c->flags,
              (unsigned long long)c->partial_render_ta_3d_fence.ufo_addr.addr,
              c->partial_render_ta_3d_fence.value);
   }

   if (!strcmp(tag, "3D") && size >= 16) {
      const struct rogue_fwif_cmd_3d *c = data;
      const struct rogue_fwif_3d_regs *r = &c->regs;

      fprintf(stderr,
              "pvr-3d usc_out=%08x clear=%08x,%08x,%08x,%08x bgdepth=%08x "
              "bgvals=%08x aa=%08x xtp=%08x ctl=%08x tpu=%08x pdsinfo=%08x "
              "pdsdata=%08x view=%08x\\n",
              r->usc_pixel_output_ctrl,
              r->usc_clear_register[0], r->usc_clear_register[1],
              r->usc_clear_register[2], r->usc_clear_register[3],
              r->isp_bgobjdepth, r->isp_bgobjvals, r->isp_aa,
              r->isp_xtp_pipe_enable, r->isp_ctl, r->tpu,
              r->event_pixel_pds_info, r->event_pixel_pds_data, r->view_idx);
      fprintf(stderr,
              "pvr-3d scissor=%llx dbias=%llx oclq=%llx zlsctl=%llx "
              "zload=%llx sten=%llx fbcdc=%llx tpub=%llx\\n",
              (unsigned long long)r->isp_scissor_base,
              (unsigned long long)r->isp_dbias_base,
              (unsigned long long)r->isp_oclqry_base,
              (unsigned long long)r->isp_zlsctl,
              (unsigned long long)r->isp_zload_store_base,
              (unsigned long long)r->isp_stencil_load_store_base,
              (unsigned long long)r->fb_cdc_zls,
              (unsigned long long)r->tpu_border_colour_table);
      fprintf(stderr,
              "pvr-3d pdsbgnd=%llx,%llx,%llx prbgnd=%llx,%llx,%llx "
              "flags=%08x zls=%08x sls=%08x exec=%08x\\n",
              (unsigned long long)r->pds_bgnd[0],
              (unsigned long long)r->pds_bgnd[1],
              (unsigned long long)r->pds_bgnd[2],
              (unsigned long long)r->pds_pr_bgnd[0],
              (unsigned long long)r->pds_pr_bgnd[1],
              (unsigned long long)r->pds_pr_bgnd[2],
              c->flags, c->zls_stride, c->sls_stride, c->execute_count);
   }

   for (uint32_t off = 0; off < size; off += 16) {
      fprintf(stderr, "pvr-cmd-%s %04x:", tag, off);"""
    assert s.count(old) == 1
    s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched named ta/3d dump")
