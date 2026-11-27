#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_cmd_buffer.c")
s = P.read_text(encoding="utf-8")

start = s.find("static void\npvr_cmd_buffer_fill_default_scissor(")
assert start >= 0
end = s.find("static VkResult\npvr_cmd_buffer_upload_tables(", start)
assert end > start
s = s[:start] + s[end:]

s = s.replace("   /* default scissor table disabled for the 1.13 draw test */\n", "", 1)

P.write_text(s, encoding="utf-8")
print("removed default scissor probe")
