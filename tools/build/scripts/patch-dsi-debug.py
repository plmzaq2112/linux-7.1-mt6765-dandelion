import sys

p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/gpu/drm/mediatek/mtk_dsi.c"
s = open(p).read()

old = """	dsi->data_rate = DIV_ROUND_UP_ULL(dsi->vm.pixelclock * bit_per_pixel,
					  dsi->lanes);

	ret = clk_set_rate(dsi->hs_clk, dsi->data_rate);
	if (ret < 0) {
		dev_err(dev, "Failed to set data rate: %d\\n", ret);
		goto err_refcount;
	}

	phy_power_on(dsi->phy);
"""

new = """	dsi->data_rate = DIV_ROUND_UP_ULL(dsi->vm.pixelclock * bit_per_pixel,
					  dsi->lanes);

	dev_info(dev, "poweron: pixelclock=%lu bpp=%u lanes=%u data_rate=%u\\n",
		 dsi->vm.pixelclock, bit_per_pixel, dsi->lanes, dsi->data_rate);

	ret = clk_set_rate(dsi->hs_clk, dsi->data_rate);
	if (ret < 0) {
		dev_err(dev, "Failed to set data rate: %d\\n", ret);
		goto err_refcount;
	}
	dev_info(dev, "hs_clk requested=%u actual=%lu\\n", dsi->data_rate,
		 clk_get_rate(dsi->hs_clk));

	ret = phy_power_on(dsi->phy);
	if (ret < 0)
		dev_err(dev, "phy_power_on failed: %d\\n", ret);
"""

if old not in s:
    sys.exit("mtk_dsi pattern not found")
open(p, "w").write(s.replace(old, new))
print("mtk_dsi instrumented")
