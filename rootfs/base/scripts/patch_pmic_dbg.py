import re, os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/keyboard/mtk-pmic-keys.c")
src = open(p).read()

old = """	regmap_read(info->keys->regmap, info->regs->deb_reg, &key_deb);

	key_deb &= info->regs->deb_mask;

	pressed = !key_deb;
"""
new = """	regmap_read(info->keys->regmap, info->regs->deb_reg, &key_deb);

	raw = key_deb;
	key_deb &= info->regs->deb_mask;

	pressed = !key_deb;

	dev_info(info->keys->dev,
		 "DANDELION key irq=%d code=%d raw=0x%x mask=0x%x deb=0x%x pressed=%d\\n",
		 irq, info->keycode, raw, info->regs->deb_mask, key_deb, pressed);
"""

if old not in src:
    raise SystemExit("handler pattern not found")

src = src.replace(old, new, 1)

# declare raw
src = src.replace("\tu32 key_deb, pressed;\n", "\tu32 key_deb, pressed, raw;\n", 1)

open(p, "w").write(src)
print("patched", p)
