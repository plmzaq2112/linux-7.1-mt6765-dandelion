#!/usr/bin/env python3
"""FT8006S panel backlight over DSI 0x51, debounced.

Applied to the pristine panel driver (dist/panel-ft8006s.c copy).
- brightness written once after the slider settles (60 ms)
- visible minimum 0x08 (never fully off), default 0x78
"""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c")
s = P.read_text(encoding="utf-8")

# 1. include
old = "#include <linux/delay.h>\n"
new = "#include <linux/backlight.h>\n#include <linux/delay.h>\n"
assert s.count(old) == 1, "include"
s = s.replace(old, new, 1)

# 2. state
old = "\tstruct gpio_desc *backlight_gpio;\n\tbool prepared;\n"
new = ("\tstruct gpio_desc *backlight_gpio;\n"
       "\tstruct backlight_device *bl;\n"
       "\tstruct delayed_work bl_work;\n"
       "\tunsigned int bl_val;\n"
       "\tunsigned int bl_applied;\n"
       "\tbool prepared;\n")
assert s.count(old) == 1, "state"
s = s.replace(old, new, 1)

# 3. debounced update + ops
old = "static const struct drm_panel_funcs ft8006s_panel_funcs = {"
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

	/* keep a visible minimum, DSI 0x00 goes black */
	if (val < 0x08)
		val = 0x08;

	ctx->bl_val = val;
	/* coalesce slider drags: only the settled value reaches the panel */
	mod_delayed_work(system_wq, &ctx->bl_work, msecs_to_jiffies(60));

	return 0;
}

static const struct backlight_ops ft8006s_bl_ops = {
	.update_status = ft8006s_bl_update_status,
};

static const struct drm_panel_funcs ft8006s_panel_funcs = {"""
assert s.count(old) == 1, "ops"
s = s.replace(old, new, 1)

# 4. apply brightness after prepare
old = "\tctx->prepared = true;\n\n\treturn 0;\n}"
new = ("\tctx->prepared = true;\n\tctx->bl_applied = 0;\n\n"
       "\tif (ctx->bl)\n\t\tbacklight_update_status(ctx->bl);\n\n\treturn 0;\n}")
assert s.count(old) == 1, "prepare"
s = s.replace(old, new, 1)

# 5. register device in probe
old = """	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;"""
new = """	struct backlight_properties props = {
		.type = BACKLIGHT_RAW,
		.max_brightness = 0xff,
		.brightness = 0x78,
	};

	INIT_DELAYED_WORK(&ctx->bl_work, ft8006s_bl_work);

	ctx->bl = devm_backlight_device_register(dev, "panel-backlight",
						 dev, ctx,
						 &ft8006s_bl_ops, &props);
	if (IS_ERR(ctx->bl))
		return dev_err_probe(dev, PTR_ERR(ctx->bl), "backlight register\\n");

	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;"""
assert s.count(old) == 1, "probe"
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("panel backlight patched (debounce 60ms, min 0x08, default 0x78)")
