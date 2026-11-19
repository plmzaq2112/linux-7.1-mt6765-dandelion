// SPDX-License-Identifier: GPL-2.0
/*
 * Fitipower FT8006S DSI panel (Redmi 9A / dandelion)
 *
 * Timing and init sequence taken from the vendor LCM driver
 * ft8006s_vdo_hdp_boe_helitai (4.19 tree).
 */

#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>
#include <linux/of.h>

#include <video/mipi_display.h>

#include <drm/drm_mipi_dsi.h>
#include <drm/drm_modes.h>
#include <drm/drm_panel.h>

struct ft8006s {
	struct drm_panel panel;
	struct mipi_dsi_device *dsi;
	struct gpio_desc *reset_gpio;
	struct gpio_desc *enable_gpio;
	struct gpio_desc *biasp_gpio;
	struct gpio_desc *biasn_gpio;
	struct gpio_desc *backlight_gpio;
	bool prepared;
};

static inline struct ft8006s *panel_to_ft8006s(struct drm_panel *panel)
{
	return container_of(panel, struct ft8006s, panel);
}

static const struct drm_display_mode ft8006s_mode = {
	.clock		= 87900,
	.hdisplay	= 720,
	.hsync_start	= 720 + 48,
	.hsync_end	= 720 + 48 + 16,
	.htotal		= 720 + 48 + 16 + 45,
	.vdisplay	= 1600,
	.vsync_start	= 1600 + 115,
	.vsync_end	= 1600 + 115 + 8,
	.vtotal		= 1600 + 115 + 8 + 45,
	.width_mm	= 68,
	.height_mm	= 151,
	.type		= DRM_MODE_TYPE_DRIVER | DRM_MODE_TYPE_PREFERRED,
};

static int ft8006s_write(struct ft8006s *ctx, u8 cmd, const u8 *data, size_t len)
{
	return mipi_dsi_dcs_write(ctx->dsi, cmd, data, len);
}

static int ft8006s_init_sequence(struct ft8006s *ctx)
{
	int ret;

	ret = ft8006s_write(ctx, 0x41, (const u8[]){0x5a, 0x19}, 2);
	if (ret < 0)
		return ret;

	ret = ft8006s_write(ctx, 0xa0, (const u8[]){0x05, 0x05, 0x02, 0x00}, 4);
	if (ret < 0)
		return ret;

	ret = ft8006s_write(ctx, 0x41, (const u8[]){0x5a, 0x24}, 2);
	if (ret < 0)
		return ret;

	ret = ft8006s_write(ctx, 0x42, (const u8[]){0x24}, 1);
	if (ret < 0)
		return ret;

	ret = ft8006s_write(ctx, 0x8d, (const u8[]){0x5a}, 1);
	if (ret < 0)
		return ret;

	ret = ft8006s_write(ctx, 0x41, (const u8[]){0x5a, 0x2f}, 2);
	if (ret < 0)
		return ret;

	ret = ft8006s_write(ctx, 0x19, (const u8[]){0x01}, 1);
	if (ret < 0)
		return ret;

	ret = ft8006s_write(ctx, 0x4c, (const u8[]){0x03}, 1);
	if (ret < 0)
		return ret;

	ret = mipi_dsi_dcs_exit_sleep_mode(ctx->dsi);
	if (ret < 0)
		return ret;

	msleep(120);

	ret = mipi_dsi_dcs_set_display_on(ctx->dsi);
	if (ret < 0)
		return ret;

	/* brightness: 0xff = max, CABC off */
	ret = ft8006s_write(ctx, 0x51, (const u8[]){0xff}, 1);
	if (ret < 0)
		return ret;

	ret = ft8006s_write(ctx, 0x53, (const u8[]){0x2c}, 1);
	if (ret < 0)
		return ret;

	ret = ft8006s_write(ctx, 0x55, (const u8[]){0x00}, 1);
	if (ret < 0)
		return ret;

	msleep(5);

	return 0;
}

static int ft8006s_prepare(struct drm_panel *panel)
{
	struct ft8006s *ctx = panel_to_ft8006s(panel);
	int ret;

	if (ctx->prepared)
		return 0;

	if (ctx->enable_gpio)
		gpiod_set_value_cansleep(ctx->enable_gpio, 1);

	if (ctx->reset_gpio)
		gpiod_set_value_cansleep(ctx->reset_gpio, 0);
	msleep(5);

	if (ctx->biasp_gpio)
		gpiod_set_value_cansleep(ctx->biasp_gpio, 1);
	msleep(2);
	if (ctx->biasn_gpio)
		gpiod_set_value_cansleep(ctx->biasn_gpio, 1);
	msleep(9);

	if (ctx->reset_gpio)
		gpiod_set_value_cansleep(ctx->reset_gpio, 1);
	msleep(35);

	ret = ft8006s_init_sequence(ctx);
	if (ret < 0) {
		dev_err(&ctx->dsi->dev, "init sequence failed: %d\n", ret);
		return ret;
	}

	ctx->prepared = true;

	return 0;
}

static int ft8006s_enable(struct drm_panel *panel)
{
	struct ft8006s *ctx = panel_to_ft8006s(panel);

	if (ctx->backlight_gpio)
		gpiod_set_value_cansleep(ctx->backlight_gpio, 1);

	return 0;
}

static int ft8006s_disable(struct drm_panel *panel)
{
	struct ft8006s *ctx = panel_to_ft8006s(panel);

	if (ctx->backlight_gpio)
		gpiod_set_value_cansleep(ctx->backlight_gpio, 0);

	mipi_dsi_dcs_set_display_off(ctx->dsi);

	return 0;
}

static int ft8006s_unprepare(struct drm_panel *panel)
{
	struct ft8006s *ctx = panel_to_ft8006s(panel);

	if (!ctx->prepared)
		return 0;

	mipi_dsi_dcs_enter_sleep_mode(ctx->dsi);

	if (ctx->reset_gpio)
		gpiod_set_value_cansleep(ctx->reset_gpio, 0);

	if (ctx->biasn_gpio)
		gpiod_set_value_cansleep(ctx->biasn_gpio, 0);
	if (ctx->biasp_gpio)
		gpiod_set_value_cansleep(ctx->biasp_gpio, 0);

	ctx->prepared = false;

	return 0;
}

static int ft8006s_get_modes(struct drm_panel *panel, struct drm_connector *connector)
{
	struct ft8006s *ctx = panel_to_ft8006s(panel);
	struct drm_display_mode *mode;

	mode = drm_mode_duplicate(connector->dev, &ft8006s_mode);
	if (!mode)
		return -ENOMEM;

	drm_mode_set_name(mode);
	mode->type = DRM_MODE_TYPE_DRIVER | DRM_MODE_TYPE_PREFERRED;
	connector->display_info.width_mm = mode->width_mm;
	connector->display_info.height_mm = mode->height_mm;
	drm_mode_probed_add(connector, mode);

	return 1;
}

static const struct drm_panel_funcs ft8006s_panel_funcs = {
	.prepare = ft8006s_prepare,
	.enable = ft8006s_enable,
	.disable = ft8006s_disable,
	.unprepare = ft8006s_unprepare,
	.get_modes = ft8006s_get_modes,
};

static int ft8006s_probe(struct mipi_dsi_device *dsi)
{
	struct device *dev = &dsi->dev;
	struct ft8006s *ctx;
	int ret;

	ctx = devm_drm_panel_alloc(dev, struct ft8006s, panel,
				   &ft8006s_panel_funcs,
				   DRM_MODE_CONNECTOR_DSI);
	if (IS_ERR(ctx))
		return PTR_ERR(ctx);

	ctx->dsi = dsi;

	ctx->reset_gpio = devm_gpiod_get_optional(dev, "reset", GPIOD_OUT_LOW);
	if (IS_ERR(ctx->reset_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->reset_gpio), "reset gpio\n");

	ctx->enable_gpio = devm_gpiod_get_optional(dev, "enable", GPIOD_OUT_HIGH);
	if (IS_ERR(ctx->enable_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->enable_gpio), "enable gpio\n");

	ctx->biasp_gpio = devm_gpiod_get_optional(dev, "biasp", GPIOD_OUT_LOW);
	if (IS_ERR(ctx->biasp_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->biasp_gpio), "biasp gpio\n");

	ctx->biasn_gpio = devm_gpiod_get_optional(dev, "biasn", GPIOD_OUT_LOW);
	if (IS_ERR(ctx->biasn_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->biasn_gpio), "biasn gpio\n");

	ctx->backlight_gpio = devm_gpiod_get_optional(dev, "backlight", GPIOD_OUT_LOW);
	if (IS_ERR(ctx->backlight_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->backlight_gpio), "backlight gpio\n");

	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;
	dsi->mode_flags = MIPI_DSI_MODE_VIDEO | MIPI_DSI_MODE_VIDEO_SYNC_PULSE |
			  MIPI_DSI_MODE_LPM;

	mipi_dsi_set_drvdata(dsi, ctx);

	drm_panel_add(&ctx->panel);

	ret = mipi_dsi_attach(dsi);
	if (ret < 0) {
		drm_panel_remove(&ctx->panel);
		return ret;
	}

	return 0;
}

static void ft8006s_remove(struct mipi_dsi_device *dsi)
{
	struct ft8006s *ctx = mipi_dsi_get_drvdata(dsi);

	mipi_dsi_detach(dsi);
	drm_panel_remove(&ctx->panel);
}

static const struct of_device_id ft8006s_of_match[] = {
	{ .compatible = "fitipower,ft8006s" },
	{ }
};
MODULE_DEVICE_TABLE(of, ft8006s_of_match);

static struct mipi_dsi_driver ft8006s_driver = {
	.probe = ft8006s_probe,
	.remove = ft8006s_remove,
	.driver = {
		.name = "panel-fitipower-ft8006s",
		.of_match_table = ft8006s_of_match,
	},
};
module_mipi_dsi_driver(ft8006s_driver);

MODULE_AUTHOR("dandelion mainline");
MODULE_DESCRIPTION("Fitipower FT8006S DSI panel");
MODULE_LICENSE("GPL");
