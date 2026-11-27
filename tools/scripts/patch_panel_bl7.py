#!/usr/bin/env python3
"""Drop the debounce: write DSI 0x51 immediately on every brightness update."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c")
s = P.read_text(encoding="utf-8")

# 1. struct: drop delayed work + pending value
old = ("\tstruct backlight_device *bl;\n"
       "\tstruct delayed_work bl_work;\n"
       "\tunsigned int bl_val;\n"
       "\tunsigned int bl_applied;\n")
new = ("\tstruct backlight_device *bl;\n"
       "\tunsigned int bl_applied;\n")
assert s.count(old) == 1, "struct"
s = s.replace(old, new, 1)

# 2. replace worker + debounced update with direct write
old = """static void ft8006s_bl_work(struct work_struct *work)
{
	struct ft8006s *ctx = container_of(work, struct ft8006s, bl_work.work);
	u8 val = ctx->bl_val;

	if (!ctx->prepared)
		return;
	if (val == ctx->bl_applied)
		return;

	ctx->bl_applied = val;
	ft8006s_write(ctx, 0x51, (const u8[]){val >> 3, (val & 0x07) << 1}, 2);
}

static int ft8006s_bl_update_status(struct backlight_device *bl)
{
	struct ft8006s *ctx = bl_get_data(bl);
	unsigned int val = backlight_get_brightness(bl);

	/* keep a visible minimum, 0x00 goes black */
	if (val < 0x40)
		val = 0x40;

	ctx->bl_val = val;
	/* coalesce slider drags: only the settled value reaches the panel */
	mod_delayed_work(system_wq, &ctx->bl_work, msecs_to_jiffies(25));

	return 0;
}
"""
new = """static int ft8006s_bl_update_status(struct backlight_device *bl)
{
	struct ft8006s *ctx = bl_get_data(bl);
	unsigned int val = backlight_get_brightness(bl);

	/* keep a visible minimum, 0x00 goes black */
	if (val < 0x40)
		val = 0x40;

	if (!ctx->prepared)
		return 0;
	if (val == ctx->bl_applied)
		return 0;

	ctx->bl_applied = val;
	ft8006s_write(ctx, 0x51, (const u8[]){val >> 3, (val & 0x07) << 1}, 2);

	return 0;
}
"""
assert s.count(old) == 1, "worker"
s = s.replace(old, new, 1)

# 3. probe: no workqueue init
old = "\tINIT_DELAYED_WORK(&ctx->bl_work, ft8006s_bl_work);\n\n"
assert s.count(old) == 1, "init work"
s = s.replace(old, "", 1)

P.write_text(s, encoding="utf-8")
print("debounce removed: immediate 0x51 writes")
