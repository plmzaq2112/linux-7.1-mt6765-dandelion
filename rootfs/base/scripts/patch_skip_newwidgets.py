import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/sound/soc/mediatek/common/mtk-afe-platform-driver.c")
s = open(p).read()

if "skip new_widgets in component probe" in s:
    print("already patched")
    raise SystemExit

old = """	dev_info(afe->dev, "DANDELION subdai: new_widgets enter\\n");
	snd_soc_dapm_new_widgets(component->card);
	dev_info(afe->dev, "DANDELION subdai: new_widgets done\\n");"""

new = """	/* skip new_widgets in component probe; the card bind does it later */
	dev_info(afe->dev, "DANDELION subdai: done (new_widgets skipped)\\n");"""

assert old in s, "new_widgets block not found"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("skipped new_widgets in component probe")
