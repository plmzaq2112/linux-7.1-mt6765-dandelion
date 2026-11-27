#!/usr/bin/env python3
"""Raise panel backlight ceiling to the full 11-bit range (2047)."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c")
s = P.read_text(encoding="utf-8")

old = "\t/* 11-bit brightness, full scale 1472 (vendor 2047 feature) */\n\tret = ft8006s_write(ctx, 0x51, (const u8[]){0xb8, 0x00}, 2);\n"
new = ("\t/* 11-bit brightness, full 2047 range */\n"
       "\tret = ft8006s_write(ctx, 0x51, (const u8[]){0xff, 0x06}, 2);\n")
assert s.count(old) == 1, "init"
s = s.replace(old, new, 1)

old = "\t\t.max_brightness = 0x5c0,\n"
new = "\t\t.max_brightness = 0x7ff,\n"
assert s.count(old) == 1, "props"
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("backlight ceiling -> 2047 (0x7ff)")
