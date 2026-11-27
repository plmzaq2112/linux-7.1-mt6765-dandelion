#!/usr/bin/env python3
"""FT8006S backlight: 11-bit DSI 0x51 (vendor CONFIG_BACKLIGHT_SUPPORT_2047_FEATURE).

Vendor encoding:
    level = ui * 72 / 100; level <<= 1;
    para[0] = level >> 4;   para[1] = level & 0x0e;
=> v = (b0 << 3) | (b1 >> 1), full scale ~1472.
"""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c")
s = P.read_text(encoding="utf-8")

# init sequence: max 11-bit level (1472 -> 0xb8, 0x00)
old = "\t/* vendor LCM ceiling is 0xb8 (see lcm_setbacklight_cmdq) */\n\tret = ft8006s_write(ctx, 0x51, (const u8[]){0xb8}, 1);\n"
new = ("\t/* 11-bit brightness, full scale 1472 (vendor 2047 feature) */\n"
       "\tret = ft8006s_write(ctx, 0x51, (const u8[]){0xb8, 0x00}, 2);\n")
assert s.count(old) == 1, "init"
s = s.replace(old, new, 1)

# work: send two bytes
old = """	ctx->bl_applied = val;
	ft8006s_write(ctx, 0x51, &val, 1);
"""
new = """	ctx->bl_applied = val;
	ft8006s_write(ctx, 0x51, (const u8[]){val >> 3, (val & 0x07) << 1}, 2);
"""
assert s.count(old) == 1, "work"
s = s.replace(old, new, 1)

# min / debounce
old = """	/* keep a visible minimum, DSI 0x00 goes black */
	if (val < 0x08)
		val = 0x08;
"""
new = """	/* keep a visible minimum, 0x00 goes black */
	if (val < 0x40)
		val = 0x40;
"""
assert s.count(old) == 1, "min"
s = s.replace(old, new, 1)

old = "msecs_to_jiffies(60)"
new = "msecs_to_jiffies(25)"
assert s.count(old) == 1, "debounce"
s = s.replace(old, new, 1)

# props: 11-bit range
old = "\t\t.max_brightness = 0xb8,\n\t\t.brightness = 0x78,\n"
new = "\t\t.max_brightness = 0x5c0,\n\t\t.brightness = 0x400,\n"
assert s.count(old) == 1, "props"
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("11-bit backlight applied (max 1472, default 1024, min 64, debounce 25ms)")
