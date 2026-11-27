#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c")
s = P.read_text(encoding="utf-8")

# add work struct
old = "\tstruct backlight_device *bl;\n\tbool prepared;\n"
new = ("\tstruct backlight_device *bl;\n"
       "\tstruct delayed_work bl_work;\n"
       "\tunsigned int bl_val;\n"
       "\tunsigned int bl_applied;\n"
       "\tbool prepared;\n")
assert s.count(old) == 1
s = s.replace(old, new, 1)

# replace backlight update
old = """static int ft8006s_bl_update_status(struct backlight_device *bl)
{
	struct ft8006s *ctx = bl_get_data(bl);
	u8 val = backlight_get_brightness(bl);

	if (!ctx->prepared)
		return 0;

	return ft8006s_write(ctx, 0x51, &val, 1);
}
"""
new = """static void ft8006s_bl_work(struct work_struct *work)
{
	struct ft8006s *ctx = container_of(work, struct ft8006s, bl_work.work);
	u8 val = ctx->bl_val;

	if (!ctx->prepared)
		return;
	if (val == ctx->bl_applied)
		return;

	ctx->bl_applied = val;
	ft8006s_write(ctx, 0x51, &val, 1);
}

static int ft8006s_bl_update_status(struct backlight_device *bl)
{
	struct ft8006s *ctx = bl_get_data(bl);
	unsigned int val = backlight_get_brightness(bl);

	/* keep a visible minimum (DSI 0x00 would be too dark) */
	if (val < 0x08)
		val = 0x08;

	ctx->bl_val = val;
	mod_delayed_work(system_wq, &ctx->bl_work, msecs_to_jiffies(40));

	return 0;
}
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

# default brightness
old = """		.max_brightness = 0xff,
		.brightness = 0xff,
"""
new = """		.max_brightness = 0xff,
		.brightness = 0x78,
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

# init workqueue in probe (before backlight register)
old = """	ctx->bl = devm_backlight_device_register(dev, "panel-backlight","""
new = """	INIT_DELAYED_WORK(&ctx->bl_work, ft8006s_bl_work);

	ctx->bl = devm_backlight_device_register(dev, "panel-backlight","""
assert s.count(old) == 1
s = s.replace(old, new, 1)

# apply at prepare
old = """	ctx->prepared = true;

	if (ctx->bl)
		backlight_update_status(ctx->bl);
"""
new = """	ctx->prepared = true;
	ctx->bl_applied = 0;

	if (ctx->bl)
		backlight_update_status(ctx->bl);
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("debounce patched")
