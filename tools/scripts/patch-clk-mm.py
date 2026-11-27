import sys

p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/clk/mediatek/clk-mt6765-mm.c"
s = open(p).read()

old = '''static const struct of_device_id of_match_clk_mt6765_mm[] = {
	{
		.compatible = "mediatek,mt6765-mmsys",
		.data = &mm_desc,
	}, {
		/* sentinel */
	}
};
MODULE_DEVICE_TABLE(of, of_match_clk_mt6765_mm);

static struct platform_driver clk_mt6765_mm_drv = {
	.probe = mtk_clk_simple_probe,
	.remove = mtk_clk_simple_remove,
	.driver = {
		.name = "clk-mt6765-mm",
		.of_match_table = of_match_clk_mt6765_mm,
	},
};
'''

new = '''static const struct platform_device_id clk_mt6765_mm_id_table[] = {
	{ .name = "clk-mt6765-mm", .driver_data = (kernel_ulong_t)&mm_desc },
	{ /* sentinel */ }
};
MODULE_DEVICE_TABLE(platform, clk_mt6765_mm_id_table);

static struct platform_driver clk_mt6765_mm_drv = {
	.probe = mtk_clk_pdev_probe,
	.remove = mtk_clk_pdev_remove,
	.driver = {
		.name = "clk-mt6765-mm",
	},
	.id_table = clk_mt6765_mm_id_table,
};
'''

if old not in s:
    sys.exit("pattern not found")
open(p, "w").write(s.replace(old, new))
print("patched")
