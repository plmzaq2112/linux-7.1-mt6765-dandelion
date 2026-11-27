import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/sound/soc/mediatek/common/mtk-afe-platform-driver.c")
s = open(p).read()

if "DANDELION subdai" in s:
    print("already patched")
    raise SystemExit

old = """	list_for_each_entry(dai, &afe->sub_dais, list) {
		if (dai->controls)
			snd_soc_add_component_controls(component,
						       dai->controls,
						       dai->num_controls);

		if (dai->dapm_widgets)
			snd_soc_dapm_new_controls(dapm,
						  dai->dapm_widgets,
						  dai->num_dapm_widgets);
	}
	/* add routes after all widgets are added */
	list_for_each_entry(dai, &afe->sub_dais, list) {
		if (dai->dapm_routes)
			snd_soc_dapm_add_routes(dapm,
						dai->dapm_routes,
						dai->num_dapm_routes);
	}

	snd_soc_dapm_new_widgets(component->card);
"""
new = """	dev_info(afe->dev, "DANDELION subdai: controls/widgets loop\\n");
	list_for_each_entry(dai, &afe->sub_dais, list) {
		if (dai->controls)
			snd_soc_add_component_controls(component,
						       dai->controls,
						       dai->num_controls);

		if (dai->dapm_widgets)
			snd_soc_dapm_new_controls(dapm,
						  dai->dapm_widgets,
						  dai->num_dapm_widgets);
	}
	dev_info(afe->dev, "DANDELION subdai: routes loop\\n");
	/* add routes after all widgets are added */
	list_for_each_entry(dai, &afe->sub_dais, list) {
		if (dai->dapm_routes)
			snd_soc_dapm_add_routes(dapm,
						dai->dapm_routes,
						dai->num_dapm_routes);
	}

	dev_info(afe->dev, "DANDELION subdai: new_widgets enter\\n");
	snd_soc_dapm_new_widgets(component->card);
	dev_info(afe->dev, "DANDELION subdai: new_widgets done\\n");
"""
assert old in s, "sub dai block not found"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("patched subdai diagnostics")
