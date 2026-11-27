#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c")
s = P.read_text(encoding="utf-8")

# include
old = "#include <linux/delay.h>\n"
new = "#include <linux/backlight.h>\n#include <linux/delay.h>\n"
assert s.count(old) == 1
s = s.replace(old, new, 1)

# state
old = "\tstruct gpio_desc *backlight_gpio;\n\tbool prepared;\n"
new = "\tstruct gpio_desc *backlight_gpio;\n\tstruct backlight_device *bl;\n\tbool prepared;\n"
assert s.count(old) == 1
s = s.replace(old, new, 1)

# ops before panel funcs
old = "static const struct drm_panel_funcs ft8006s_panel_funcs = {"
new = """static int ft8006s_bl_update_status(struct backlight_device *bl)
{
	struct ft8006s *ctx = bl_get_data(bl);
	u8 val = backlight_get_brightness(bl);

	if (!ctx->prepared)
		return 0;

	return ft8006s_write(ctx, 0x51, &val, 1);
}

static const struct backlight_ops ft8006s_bl_ops = {
	.update_status = ft8006s_bl_update_status,
};

static const struct drm_panel_funcs ft8006s_panel_funcs = {"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

# apply current brightness after init
old = "\tctx->prepared = true;\n\n\treturn 0;\n}"
new = "\tctx->prepared = true;\n\n\tif (ctx->bl)\n\t\tbacklight_update_status(ctx->bl);\n\n\treturn 0;\n}"
assert s.count(old) == 1
s = s.replace(old, new, 1)

# register backlight in probe
old = """	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;"""
new = """	struct backlight_properties props = {
		.type = BACKLIGHT_RAW,
		.max_brightness = 0xff,
		.brightness = 0xff,
	};

	ctx->bl = devm_backlight_device_register(dev, "panel-backlight",
						 dev, ctx,
						 &ft8006s_bl_ops, &props);
	if (IS_ERR(ctx->bl))
		return dev_err_probe(dev, PTR_ERR(ctx->bl), "backlight register\\n");

	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("panel backlight patched")
