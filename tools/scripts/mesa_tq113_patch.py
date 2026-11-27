#!/usr/bin/env python3
"""Pack Mesa's 192-byte transfer command into the 1.13 152-byte layout.

1.13 CMDTRANSFER (from the TQ golden):
  0x00 isp_bgobjvals
  0x04 usc_pixel_output_ctrl
  0x08 usc_clear_register0..3
  0x18 isp_mtile_size
  0x1c isp_render_origin
  0x20 isp_ctl
  0x24 isp_xtp_pipe_enable
  0x28 event_pixel_pds_info
  0x2c event_pixel_pds_code
  0x30 event_pixel_pds_data
  0x34 isp_render
  0x38 isp_rgn
  0x40 pds_bgnd0_base
  0x48 pds_bgnd1_base
  0x50 pds_bgnd3_sizeinfo
  0x58 isp_mtile_base
  0x60 pbe_wordx_mrty[2][3]   (2 RTs * 3 u64)
  0x90 flags
Mesa's struct has an extra isp_aa at 0x28 (shifting pds info) and 3 RTs
(72 bytes) in pbe_wordx_mrty.
"""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_transfer.c")
s = P.read_text(encoding="utf-8")

if "pvr_pack_cmd_transfer_113" in s:
    print("already patched")
    raise SystemExit(0)

anchor = """static void pvr_srv_transfer_cmds_init(
"""
packer = r"""#define PVR_CMDTRANSFER_113_SIZE 152

static void pvr_pack_cmd_transfer_113(uint8_t dst[PVR_CMDTRANSFER_113_SIZE],
                                      const struct rogue_fwif_cmd_transfer *src)
{
   memset(dst, 0, PVR_CMDTRANSFER_113_SIZE);

   /* 0x00..0x27: bgobjvals .. isp_xtp_pipe_enable (10 u32). */
   memcpy(dst + 0x00, &src->regs, 0x28);

   /* 0x28..0x3b: 1.13 has no isp_aa, so pds info/code/data and
    * isp_render/isp_rgn move up one slot. */
   memcpy(dst + 0x28, &src->regs.event_pixel_pds_info, 4);
   memcpy(dst + 0x2c, &src->regs.event_pixel_pds_code, 4);
   memcpy(dst + 0x30, &src->regs.event_pixel_pds_data, 4);
   memcpy(dst + 0x34, &src->regs.isp_render, 4);
   memcpy(dst + 0x38, &src->regs.isp_rgn, 4);

   /* 0x40..0x5f: pds_bgnd0/1/3 + isp_mtile_base. */
   memcpy(dst + 0x40, &src->regs.pds_bgnd0_base, 24);
   memcpy(dst + 0x58, &src->regs.isp_mtile_base, 8);

   /* 0x60..0x8f: pbe_wordx_mrty for 2 RTs. */
   memcpy(dst + 0x60, &src->regs.pbe_wordx_mrty[0][0], 48);

   /* 0x90: flags. */
   memcpy(dst + 0x90, &src->flags, 4);
}

static void pvr_srv_transfer_cmds_init(
"""
assert s.count(anchor) == 1
s = s.replace(anchor, packer, 1)

old = """   uint32_t cmd_flags[PVR_TRANSFER_MAX_PREPARES_PER_SUBMIT] = { 0 };
   uint32_t cmd_sizes[PVR_TRANSFER_MAX_PREPARES_PER_SUBMIT];
"""
new = """   uint32_t cmd_flags[PVR_TRANSFER_MAX_PREPARES_PER_SUBMIT] = { 0 };
   uint32_t cmd_sizes[PVR_TRANSFER_MAX_PREPARES_PER_SUBMIT];
   uint8_t transfer_113[PVR_TRANSFER_MAX_PREPARES_PER_SUBMIT]
                       [PVR_CMDTRANSFER_113_SIZE];
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = """   for (uint32_t i = 0U; i < submit_info->cmd_count; i++) {
      cmd_sizes[i] = sizeof(**cmds_ptr_arr);
      cmds_ptr_arr[i] = &transfer_cmds[i];
   }
"""
new = """   for (uint32_t i = 0U; i < submit_info->cmd_count; i++) {
      pvr_pack_cmd_transfer_113(transfer_113[i], &transfer_cmds[i]);
      cmd_sizes[i] = PVR_CMDTRANSFER_113_SIZE;
      cmds_ptr_arr[i] = transfer_113[i];
   }
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched 1.13 TQ packer")
