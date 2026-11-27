import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/keyboard/mtk-pmic-keys.c")
src = open(p).read()

# 1) add delayed_work to the key info struct
old_struct = """struct mtk_pmic_keys_info {
	struct mtk_pmic_keys *keys;
	const struct mtk_pmic_keys_regs *regs;
	unsigned int keycode;
	int irq;
	int irq_r; /* optional: release irq if different */
	bool wakeup:1;
};"""
new_struct = """struct mtk_pmic_keys_info {
	struct mtk_pmic_keys *keys;
	const struct mtk_pmic_keys_regs *regs;
	unsigned int keycode;
	int irq;
	int irq_r; /* optional: release irq if different */
	bool wakeup:1;
	struct delayed_work release_work;
};"""
if old_struct not in src:
    raise SystemExit("struct pattern not found")
src = src.replace(old_struct, new_struct, 1)

# 2) insert release poll before the threaded handler
anchor = "static irqreturn_t mtk_pmic_keys_irq_handler_thread(int irq, void *data)"
poll = """static void mtk_pmic_keys_release_poll(struct work_struct *work)
{
	struct mtk_pmic_keys_info *info =
		container_of(work, struct mtk_pmic_keys_info, release_work.work);
	u32 key_deb;

	regmap_read(info->keys->regmap, info->regs->deb_reg, &key_deb);
	if (key_deb & info->regs->deb_mask) {
		input_report_key(info->keys->input_dev, info->keycode, 0);
		input_sync(info->keys->input_dev);
		dev_info(info->keys->dev,
			 "DANDELION key irq=release-poll code=%d released\\n",
			 info->keycode);
		return;
	}

	schedule_delayed_work(&info->release_work, msecs_to_jiffies(50));
}

"""
if anchor not in src:
    raise SystemExit("handler anchor not found")
src = src.replace(anchor, poll + anchor, 1)

# 3) schedule the poll when pressed
old_report = """	input_report_key(info->keys->input_dev, info->keycode, pressed);
	input_sync(info->keys->input_dev);
"""
new_report = """	input_report_key(info->keys->input_dev, info->keycode, pressed);
	input_sync(info->keys->input_dev);

	if (pressed) {
		mod_delayed_work(system_wq, &info->release_work,
				 msecs_to_jiffies(50));
	} else {
		cancel_delayed_work(&info->release_work);
	}
"""
if old_report not in src:
    raise SystemExit("report pattern not found")
src = src.replace(old_report, new_report, 1)

# 4) init the delayed work in setup
old_setup = """	info->keys = keys;

	ret = regmap_update_bits(keys->regmap, info->regs->intsel_reg,"""
new_setup = """	info->keys = keys;
	INIT_DELAYED_WORK(&info->release_work, mtk_pmic_keys_release_poll);

	ret = regmap_update_bits(keys->regmap, info->regs->intsel_reg,"""
if old_setup not in src:
    raise SystemExit("setup pattern not found")
src = src.replace(old_setup, new_setup, 1)

open(p, "w").write(src)
print("patched release poll into", p)
