#!/usr/bin/env python3
"""The vendor 1.13 UM on BVNC 22.87.104.18 reports uiRgnHeaderSize=16 for a
64x64 surface (16 region headers, 4 bytes each).  Mesa's generic helper
returns 5 bytes/header, which made the region array 20 dwords and the
firmware only rendered part of the surface.
"""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/include/hwdef/rogue_hw_utils.h")
s = P.read_text(encoding="utf-8")

if "PVR_DEV_IDENT_22_87_104_18" in s:
    print("already patched")
    raise SystemExit(0)

old = """   if (PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) &&
       version == 2) {
      return 6;
   }

   return 5;
}"""
new = """   if (PVR_HAS_FEATURE(dev_info, simple_internal_parameter_format) &&
       version == 2) {
      return 6;
   }

   /* Vendor DDK 1.13 on GE8320 (22.87.104.18) uses 4-byte region headers;
    * its uiRgnHeaderSize for a 64x64 RT is 16, not 20.
    */
   if (dev_info->ident.b == 22 && dev_info->ident.v == 87 &&
       dev_info->ident.n == 104)
      return 4;

   return 5;
}"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched region header size")
