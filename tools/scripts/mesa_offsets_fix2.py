#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv_bridge.c")
s = P.read_text(encoding="utf-8")

old = """   fprintf(stderr,
           "pvr-off cmd3d=%zu shared=%zu regs=%zu flags=%zu ufo=%zu brn=%zu\\n",
           sizeof(struct rogue_fwif_cmd_3d),
           offsetof(struct rogue_fwif_cmd_3d, cmd_shared),
           offsetof(struct rogue_fwif_cmd_3d, regs),
           offsetof(struct rogue_fwif_cmd_3d, flags),
           offsetof(struct rogue_fwif_cmd_3d, partial_render_ta_3d_fence),
           offsetof(struct rogue_fwif_cmd_3d, brn61484_66333_live_rt));"""
new = """   fprintf(stderr,
           "pvr-off cmd3d=%zu shared=%zu regs=%zu flags=%zu zls=%zu sls=%zu exec=%zu\\n",
           sizeof(struct rogue_fwif_cmd_3d),
           offsetof(struct rogue_fwif_cmd_3d, cmd_shared),
           offsetof(struct rogue_fwif_cmd_3d, regs),
           offsetof(struct rogue_fwif_cmd_3d, flags),
           offsetof(struct rogue_fwif_cmd_3d, zls_stride),
           offsetof(struct rogue_fwif_cmd_3d, sls_stride),
           offsetof(struct rogue_fwif_cmd_3d, execute_count));"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

# cmd_ta may also lack partial_render member name; keep only safe fields
old2 = """   fprintf(stderr, "pvr-off cmdta=%zu taregs=%zu taflags=%zu\\n",
           sizeof(struct rogue_fwif_cmd_ta),
           offsetof(struct rogue_fwif_cmd_ta, regs),
           offsetof(struct rogue_fwif_cmd_ta, flags));"""
assert old2 in s
P.write_text(s, encoding="utf-8")
print("fixed cmd3d offsets")
