#!/usr/bin/env python3
"""Give BVNC 22.87.104.18 (GE8320) its own device-feature block with the
simple internal parameter format disabled.

Vendor 1.13 GLES UM creates HWRTData with:
  te_screen=0x00003003 rgn=16 isp_mtile=0x00040004 stride=0x10
Mesa's simple-format path produced:
  rgn=4 isp_mtile=0x00020002 stride=0x4
so only part of a 64x64 surface was tiled.
"""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/common/device_info/ge8300.h")
s = P.read_text(encoding="utf-8")

if "pvr_device_features_22_87_104_18 =" in s:
    print("already patched")
    raise SystemExit(0)

start = s.index("static const struct pvr_device_features pvr_device_features_22_V_54_30 = {")
end = s.index("\n};", start) + len("\n};")
block = s[start:end]

new_block = block.replace("pvr_device_features_22_V_54_30",
                          "pvr_device_features_22_87_104_18")
new_block = new_block.replace(".has_simple_internal_parameter_format = true,",
                              ".has_simple_internal_parameter_format = false,")
new_block = new_block.replace(".has_simple_internal_parameter_format_v1 = true,",
                              ".has_simple_internal_parameter_format_v1 = false,")
new_block = new_block.replace(".has_simple_parameter_format_version = true,",
                              ".has_simple_parameter_format_version = false,")
new_block = new_block.replace(".simple_parameter_format_version = 1U,",
                              ".simple_parameter_format_version = 0U,")

# Insert the new features block just before the 22.87.104.18 device entry.
entry = "#define PVR_DEVICE_IDENT_22_V_104_18"
assert s.count(entry) == 1
entry_pos = s.index(entry)
s = s[:entry_pos] + new_block + "\n\n" + s[entry_pos:]

# Change only the features pointer inside pvr_device_info_22_87_104_18.
info = "static const struct pvr_device_info pvr_device_info_22_87_104_18 = {"
assert s.count(info) == 1
i = s.index(info)
head, tail = s[:i], s[i:]
assert tail.count(".features = pvr_device_features_22_V_54_30,") >= 1
tail = tail.replace(".features = pvr_device_features_22_V_54_30,",
                    ".features = pvr_device_features_22_87_104_18,", 1)
s = head + tail

P.write_text(s, encoding="utf-8")
print("patched GE8320 features")
