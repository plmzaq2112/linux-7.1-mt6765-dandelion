import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/sound/soc/soc-core.c")
s = open(p).read()

if "DANDELION soc:" in s:
    print("already patched")
    raise SystemExit

old = """	if (snd_soc_component_is_dummy(component))
		return 0;

	if (component->card) {"""
new = """	if (snd_soc_component_is_dummy(component))
		return 0;

	dev_info(component->dev, "DANDELION soc: probing component %s\\n",
		 component->name);

	if (component->card) {"""
assert old in s, "component entry anchor not found"
s = s.replace(old, new, 1)

old = """	ret = snd_soc_dapm_new_controls(dapm,
					component->driver->dapm_widgets,
					component->driver->num_dapm_widgets);
"""
new = """	ret = snd_soc_dapm_new_controls(dapm,
					component->driver->dapm_widgets,
					component->driver->num_dapm_widgets);
	dev_info(component->dev, "DANDELION soc: dapm controls ret=%d %s\\n",
		 ret, component->name);
"""
assert old in s, "dapm controls anchor not found"
s = s.replace(old, new, 1)

old = """	ret = snd_soc_component_probe(component);
	if (ret < 0)
		goto err_probe;
"""
new = """	dev_info(component->dev, "DANDELION soc: component probe enter %s\\n",
		 component->name);
	ret = snd_soc_component_probe(component);
	dev_info(component->dev, "DANDELION soc: component probe ret=%d %s\\n",
		 ret, component->name);
	if (ret < 0)
		goto err_probe;
"""
assert old in s, "component probe anchor not found"
s = s.replace(old, new, 1)

open(p, "w").write(s)
print("patched soc-core diagnostics")
