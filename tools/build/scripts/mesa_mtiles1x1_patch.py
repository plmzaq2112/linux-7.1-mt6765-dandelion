#!/usr/bin/env python3
"""Vendor 1.13 GE8320 HWRTData: tpc_size=128 (4x4 tail pointers), i.e. one
1x1 macrotile group.  Mesa's non-simple path used 4x4 macrotile groups, which
made tpc_size=2048 and left the TA/3D processing only one part of the screen.
"""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/include/hwdef/rogue_hw_utils.h")
s = P.read_text(encoding="utf-8")

if "PVR_DEV_IDENT_GE8320_1x1_MTILES" in s:
    print("already patched")
    raise SystemExit(0)

old = """   if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) ||
       version == 2) {
      *x_out = 4;
      *y_out = 4;
   } else {
      *x_out = 1;
      *y_out = 1;
   }"""
new = """   /* 1.13 GE8320 (22.87.104.18) uses a single 1x1 macrotile group:
    * vendor tpc_size is 128 (4x4 tail pointers), not 2048.
    */
   if (dev_info->ident.b == 22 && dev_info->ident.v == 87 &&
       dev_info->ident.n == 104) {
      *x_out = 1;
      *y_out = 1;
   } else if (!PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) ||
              version == 2) {
      *x_out = 4;
      *y_out = 4;
   } else {
      *x_out = 1;
      *y_out = 1;
   }"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched mtiles 1x1")
