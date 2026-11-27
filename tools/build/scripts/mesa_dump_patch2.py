#!/usr/bin/env python3
"""Add a gated hexdump of the firmware command blobs Mesa submits (line based)."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv_bridge.c")
lines = P.read_text(encoding="utf-8").splitlines(keepends=True)
text = "".join(lines)

if "pvr_dump_cmd(" not in text:
    i = lines.index("#include <stdint.h>\n")
    lines[i + 1:i + 1] = ["#include <stdio.h>\n", "#include <stdlib.h>\n"]

    j = next(k for k, l in enumerate(lines) if l.startswith("static int pvr_srv_bridge_call("))
    helper = """static bool pvr_dump_cmd_enabled(void)
{
   static int enabled = -1;

   if (enabled < 0) {
      const char *s = getenv("PVR_DUMP_CMD");

      enabled = s && s[0] && s[0] != '0';
   }

   return enabled;
}

static void pvr_dump_cmd(const char *tag, const void *data, uint32_t size)
{
   const uint8_t *b = data;

   if (!data || !size || !pvr_dump_cmd_enabled())
      return;

   for (uint32_t off = 0; off < size; off += 16) {
      fprintf(stderr, "pvr-cmd-%s %04x:", tag, off);
      for (uint32_t i = 0; i < 16 && off + i < size; i++)
         fprintf(stderr, " %02x", b[off + i]);
      fprintf(stderr, "\\n");
   }
   fprintf(stderr, "pvr-cmd-%s size=%u\\n", tag, size);
}

"""
    lines[j:j] = [helper]

    # TQ dump: before the bridge call that uses RGXSUBMITTRANSFER2
    for k, l in enumerate(lines):
        if "PVR_SRV_BRIDGE_RGXTQ_RGXSUBMITTRANSFER2," in l:
            while not lines[k].strip().startswith("int result;"):
                k -= 1
            lines.insert(k + 2, '   pvr_dump_cmd("TQ", fw_command, cmd_size);\n')
            break

    # TA/3D dump: before the return struct is initialised
    for k, l in enumerate(lines):
        if l.startswith("   struct pvr_srv_rgx_kick_ta3d2_ret ret = {"):
            lines[k:k] = ['   pvr_dump_cmd("TA", cmd_geom, cmd_geom_size);\n',
                          '   pvr_dump_cmd("3D", cmd_frag, cmd_frag_size);\n']
            break

P.write_text("".join(lines), encoding="utf-8")
print("patched")
