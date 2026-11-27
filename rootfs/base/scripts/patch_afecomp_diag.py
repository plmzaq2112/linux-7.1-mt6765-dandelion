import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/sound/soc/mediatek/common/mtk-afe-platform-driver.c")
s = open(p).read()

if "DANDELION afe comp" in s:
    print("already patched")
    raise SystemExit

old = """	snd_soc_component_init_regmap(component, afe->regmap);

	/* If the list was never initialized there are no sub-DAIs */
	if (afe->sub_dais.next && afe->sub_dais.prev) {
		ret = mtk_afe_add_sub_dai_control(component);
		if (ret)
			return ret;
	}

	return 0;"""

new = """	dev_info(afe->dev, "DANDELION afe comp: init_regmap\\n");
	snd_soc_component_init_regmap(component, afe->regmap);
	dev_info(afe->dev, "DANDELION afe comp: init_regmap done\\n");

	/* If the list was never initialized there are no sub-DAIs */
	if (afe->sub_dais.next && afe->sub_dais.prev) {
		dev_info(afe->dev, "DANDELION afe comp: adding sub dai ctl\\n");
		ret = mtk_afe_add_sub_dai_control(component);
		dev_info(afe->dev, "DANDELION afe comp: sub dai ctl ret=%d\\n", ret);
		if (ret)
			return ret;
	}

	dev_info(afe->dev, "DANDELION afe comp: done\\n");
	return 0;"""

assert old in s, "component probe body not found"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("patched afe component probe diagnostics")
