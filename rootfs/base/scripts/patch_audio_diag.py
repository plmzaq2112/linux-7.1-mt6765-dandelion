import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/sound/soc/mediatek/common/mtk-soundcard-driver.c")
s = open(p).read()

if "DANDELION audio" in s:
    print("already patched")
    raise SystemExit

old = """	if (pdata->soc_probe) {
		ret = pdata->soc_probe(soc_card_data, needs_legacy_probe);"""
new = """	dev_info(&pdev->dev, "DANDELION audio: before soc_probe\\n");
	if (pdata->soc_probe) {
		ret = pdata->soc_probe(soc_card_data, needs_legacy_probe);
		dev_info(&pdev->dev, "DANDELION audio: soc_probe ret=%d\\n", ret);"""
assert old in s, "soc_probe block not found"
s = s.replace(old, new, 1)

old2 = """	ret = devm_snd_soc_register_card(&pdev->dev, card);"""
new2 = """	dev_info(&pdev->dev, "DANDELION audio: before register_card\\n");
	ret = devm_snd_soc_register_card(&pdev->dev, card);
	dev_info(&pdev->dev, "DANDELION audio: register_card ret=%d\\n", ret);"""
assert old2 in s, "register_card not found"
s = s.replace(old2, new2, 1)

open(p, "w").write(s)
print("patched audio diagnostics")
