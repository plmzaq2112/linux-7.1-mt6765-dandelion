#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv_bridge.c")
s = P.read_text(encoding="utf-8")

old = '   pvr_dump_cmd("TQ", fw_command, cmd_size);\n'
new = """   for (uint32_t dmp_i = 0; dmp_i < prepare_count; dmp_i++)
      pvr_dump_cmd("TQ", (const uint8_t *)fw_command, cmd_size[dmp_i]);
"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8")
print("patched TQ dump loop")
