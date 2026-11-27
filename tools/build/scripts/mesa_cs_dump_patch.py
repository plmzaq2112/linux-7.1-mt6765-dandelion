#!/usr/bin/env python3
"""Dump Mesa's graphics control stream when PVR_DUMP_CS=1."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_cmd_buffer.c")
s = P.read_text(encoding="utf-8")

if "PVR_DUMP_CS" in s:
    print("already patched")
    raise SystemExit(0)

anchor = """      result = pvr_arch_csb_emit_terminate(&gfx_sub_cmd->control_stream);
      if (result != VK_SUCCESS)
         return pvr_cmd_buffer_set_error_unwarned(cmd_buffer, result);
"""
insert = """      result = pvr_arch_csb_emit_terminate(&gfx_sub_cmd->control_stream);
      if (result != VK_SUCCESS)
         return pvr_cmd_buffer_set_error_unwarned(cmd_buffer, result);

      if (getenv("PVR_DUMP_CS") && gfx_sub_cmd->control_stream.start) {
         const uint8_t *cs = gfx_sub_cmd->control_stream.start;
         uint32_t cs_len =
            (const uint8_t *)gfx_sub_cmd->control_stream.next - cs;

         fprintf(stderr, "pvr-cs len=%u\\n", cs_len);
         for (uint32_t off = 0; off < cs_len && off < 1024; off += 16) {
            fprintf(stderr, "pvr-cs %04x:", off);
            for (uint32_t i = 0; i < 16 && off + i < cs_len; i++)
               fprintf(stderr, " %02x", cs[off + i]);
            fprintf(stderr, "\\n");
         }
      }
"""
assert s.count(anchor) == 1
s = s.replace(anchor, insert, 1)

s = s.replace('#include <stdint.h>\n', '#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\n', 1)

P.write_text(s, encoding="utf-8")
print("patched control stream dump")
