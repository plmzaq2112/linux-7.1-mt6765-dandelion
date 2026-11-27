#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv_bridge.c")
s = P.read_text(encoding="utf-8")
old = """   fprintf(stderr, "pvr-off cmdtr=%zu trregs=%zu\\n",
           sizeof(struct rogue_fwif_cmd_transfer),
           offsetof(struct rogue_fwif_cmd_transfer, sTransRegs));"""
new = """   fprintf(stderr, "pvr-off cmdtr=%zu trregs=%zu trflags=%zu\\n",
           sizeof(struct rogue_fwif_cmd_transfer),
           offsetof(struct rogue_fwif_cmd_transfer, regs),
           offsetof(struct rogue_fwif_cmd_transfer, flags));"""
assert s.count(old) == 1
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8")
print("fixed")
