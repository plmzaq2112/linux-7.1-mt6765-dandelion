#!/usr/bin/env python3
"""Align panel backlight ceiling with the vendor LCM driver: 0xB8 (184)."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c")
s = P.read_text(encoding="utf-8")

old = "\t/* brightness: 0xff = max, CABC off */\n\tret = ft8006s_write(ctx, 0x51, (const u8[]){0xff}, 1);\n"
new = "\t/* vendor LCM ceiling is 0xb8 (see lcm_setbacklight_cmdq) */\n\tret = ft8006s_write(ctx, 0x51, (const u8[]){0xb8}, 1);\n"
assert s.count(old) == 1, "init 0x51"
s = s.replace(old, new, 1)

old = "\t\t.max_brightness = 0xff,\n\t\t.brightness = 0x78,\n"
new = "\t\t.max_brightness = 0xb8,\n\t\t.brightness = 0x78,\n"
assert s.count(old) == 1, "props"
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("panel brightness ceiling set to 0xb8")
