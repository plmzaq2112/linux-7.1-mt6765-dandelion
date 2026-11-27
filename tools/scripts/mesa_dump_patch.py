#!/usr/bin/env python3
"""Add a gated hexdump of the firmware command blobs Mesa submits."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv_bridge.c")
s = P.read_text(encoding="utf-8")

if "pvr_dump_cmd(" not in s:
    old = "#include <stdint.h>\n#include <string.h>\n"
    new = "#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n"
    assert s.count(old) == 1, "includes"
    s = s.replace(old, new, 1)

    old = "static int pvr_srv_bridge_call(int fd,\n"
    new = """static bool pvr_dump_cmd_enabled(void)
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

static int pvr_srv_bridge_call(int fd,
"""
    assert s.count(old) == 1, "helper anchor"
    s = s.replace(old, new, 1)

if 'pvr_dump_cmd("TQ"' not in s:
    old = """   int result;

   result = pvr_srv_bridge_call(fd,
                                 PVR_SRV_BRIDGE_RGXTQ,
                                 PVR_SRV_BRIDGE_RGXTQ_RGXSUBMITTRANSFER2,"""
    new = """   int result;

   pvr_dump_cmd("TQ", fw_command, cmd_size);

   result = pvr_srv_bridge_call(fd,
                                 PVR_SRV_BRIDGE_RGXTQ,
                                 PVR_SRV_BRIDGE_RGXTQ_RGXSUBMITTRANSFER2,"""
    assert s.count(old) == 1, "TQ anchor"
    s = s.replace(old, new, 1)

if 'pvr_dump_cmd("TA"' not in s:
    old = """   struct pvr_srv_rgx_kick_ta3d2_ret ret = {
      .error = PVR_SRV_ERROR_BRIDGE_CALL_FAILED,
      .update_fence = -1,"""
    new = """   pvr_dump_cmd("TA", cmd_geom, cmd_geom_size);
   pvr_dump_cmd("3D", cmd_frag, cmd_frag_size);

   struct pvr_srv_rgx_kick_ta3d2_ret ret = {
      .error = PVR_SRV_ERROR_BRIDGE_CALL_FAILED,
      .update_fence = -1,"""
    assert s.count(old) == 1, "TA3D anchor"
    s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched pvr_srv_bridge.c")
