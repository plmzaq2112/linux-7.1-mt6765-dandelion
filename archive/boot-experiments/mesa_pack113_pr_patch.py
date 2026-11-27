#!/usr/bin/env python3
"""Make the 1.13 submit use the kernel's combined PR+3D path.

The vendor UM passes bKickPR=1 with a NULL PR command; the 1.13 KM then
combines PR and 3D into one firmware kick.  Mesa 1.15 sends a separate PR
command, which the 1.13 firmware does not accept as-is.
"""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_arch_srv_job_render.c")
s = P.read_text(encoding="utf-8")

if "/* 1.13: let the KM combine" in s:
    print("already patched")
    raise SystemExit(0)

old = """   uint8_t geom_113[PVR_CMDTA_113_SIZE];
   uint8_t frag_113[PVR_CMD3D_113_SIZE];
   uint8_t pr_113[PVR_CMD3D_113_SIZE];
"""
new = """   uint8_t geom_113[PVR_CMDTA_113_SIZE];
   uint8_t frag_113[PVR_CMD3D_113_SIZE];
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = """   pvr_pack_cmd_3d_113(pr_113, &pr_cmd);

"""
assert s.count(old) == 1
s = s.replace(old, "", 1)

old = """                                        sizeof(geom_113),
                                        geom_113,
                                        sizeof(pr_113),
                                        pr_113,
                                        frag_cmd_size,
                                        frag_cmd_ptr,
"""
new = """                                        sizeof(geom_113),
                                        geom_113,
                                        /* 1.13: let the KM combine PR and 3D
                                         * (vendor passes no PR payload).
                                         */
                                        0,
                                        NULL,
                                        frag_cmd_size,
                                        frag_cmd_ptr,
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched combined PR/3D")
