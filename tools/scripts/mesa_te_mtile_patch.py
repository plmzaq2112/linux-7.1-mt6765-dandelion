#!/usr/bin/env python3
"""Vendor 1.13 GE8320 leaves TE_MTILE1/2 x2/x3/y2/y3 at zero; Mesa's
non-simple path programs them.  Only x1/y1 (macrotile 4x4) are used by the
1.13 firmware."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_render.c")
s = P.read_text(encoding="utf-8")

if "PVR_DEVICE_IS_GE8320_113" in s:
    print("already patched")
    raise SystemExit(0)

anchor = """static void pvr_rogue_ct_te_init(const struct pvr_device_info *dev_info,
                                 const struct pvr_rt_mtile_info *mtile_info,
                                 uint32_t samples,
                                 struct pvr_rogue_cr_te *const te_regs)
{"""
insert = """#define PVR_DEVICE_IS_GE8320_113(dev_info)          \\
   ((dev_info)->ident.b == 22 && (dev_info)->ident.v == 87 && \\
    (dev_info)->ident.n == 104)

static void pvr_rogue_ct_te_init(const struct pvr_device_info *dev_info,
                                 const struct pvr_rt_mtile_info *mtile_info,
                                 uint32_t samples,
                                 struct pvr_rogue_cr_te *const te_regs)
{"""
assert s.count(anchor) == 1
s = s.replace(anchor, insert, 1)

old = """      if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format)) {
         value.x2 = mtile_info->mtile_x2;
         value.x3 = mtile_info->mtile_x3;
      }"""
new = """      if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) &&
          !PVR_DEVICE_IS_GE8320_113(dev_info)) {
         value.x2 = mtile_info->mtile_x2;
         value.x3 = mtile_info->mtile_x3;
      }"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = """      if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format)) {
         value.y2 = mtile_info->mtile_y2;
         value.y3 = mtile_info->mtile_y3;
      }"""
new = """      if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) &&
          !PVR_DEVICE_IS_GE8320_113(dev_info)) {
         value.y2 = mtile_info->mtile_y2;
         value.y3 = mtile_info->mtile_y3;
      }"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched TE mtile legacy")
