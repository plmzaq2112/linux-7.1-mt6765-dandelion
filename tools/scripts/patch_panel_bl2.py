#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c")
s = P.read_text(encoding="utf-8")

old = """	u8 val = backlight_get_brightness(bl);

	if (!ctx->prepared)
		return 0;
"""
new = """	u8 val = backlight_get_brightness(bl);

	/* keep a visible minimum (DSI 0x00 would be too dark) */
	if (val < 0x08)
		val = 0x08;

	if (!ctx->prepared)
		return 0;
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = """		.max_brightness = 0xff,
		.brightness = 0xff,
"""
new = """		.max_brightness = 0xff,
		.brightness = 0x78,
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("panel brightness defaults patched")
