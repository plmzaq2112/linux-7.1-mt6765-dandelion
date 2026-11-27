import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/clk/mediatek/clk-mt6765-audio.c")
s = open(p).read()

if "devm_of_platform_populate" in s:
    print("already patched")
    raise SystemExit

if "#include <linux/of_platform.h>" not in s:
    s = s.replace("#include <linux/platform_device.h>",
                  "#include <linux/platform_device.h>\n#include <linux/of_platform.h>", 1)

old = """static struct platform_driver clk_mt6765_audio_drv = {
	.probe = mtk_clk_simple_probe,
	.remove = mtk_clk_simple_remove,"""
new = """static int clk_mt6765_audio_probe(struct platform_device *pdev)
{
	int r;

	r = mtk_clk_simple_probe(pdev);
	if (r)
		return r;

	r = devm_of_platform_populate(&pdev->dev);
	if (r)
		mtk_clk_simple_remove(pdev);

	return r;
}

static void clk_mt6765_audio_remove(struct platform_device *pdev)
{
	of_platform_depopulate(&pdev->dev);
	mtk_clk_simple_remove(pdev);
}

static struct platform_driver clk_mt6765_audio_drv = {
	.probe = clk_mt6765_audio_probe,
	.remove = clk_mt6765_audio_remove,"""

assert old in s, "driver block not found"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("patched audio clock driver to populate children")
