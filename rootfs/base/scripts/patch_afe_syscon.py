import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/sound/soc/mediatek/mt6765/mt6765-afe-pcm.c")
s = open(p).read()

if "syscon_node_to_regmap" in s:
    print("already patched")
    raise SystemExit

# include syscon
old_inc = "#include <linux/module.h>"
if old_inc in s:
    s = s.replace(old_inc, "#include <linux/module.h>\n#include <linux/mfd/syscon.h>", 1)

# drop the mem resource 0 ioremap
old = """	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	afe->base_addr = devm_ioremap_resource(&pdev->dev, res);
	if (IS_ERR(afe->base_addr))
		return PTR_ERR(afe->base_addr);

"""
assert old in s, "ioremap block not found"
s = s.replace(old, "", 1)

# switch to parent syscon regmap
old = """	afe->regmap = devm_regmap_init_mmio_clk(&pdev->dev, "top_audio_sel",
						afe->base_addr,
						&mt6765_afe_regmap_config);
	if (IS_ERR(afe->regmap))
		return PTR_ERR(afe->regmap);"""
new = """	afe->regmap = syscon_node_to_regmap(dev->parent->of_node);
	if (IS_ERR(afe->regmap))
		return dev_err_probe(dev, PTR_ERR(afe->regmap),
				     "could not get regmap from parent\\n");

	ret = regmap_attach_dev(dev, afe->regmap, &mt6765_afe_regmap_config);
	if (ret)
		return ret;"""
assert old in s, "regmap block not found"
s = s.replace(old, new, 1)

open(p, "w").write(s)
print("patched syscon regmap")
