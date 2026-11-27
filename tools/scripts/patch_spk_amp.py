#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/sound/soc/mediatek/mt6765/mt6765-mt6357.c")
s = P.read_text(encoding="utf-8")

old_inc = """#include <linux/array_size.h>
#include <linux/dev_printk.h>
#include <linux/err.h>
#include <linux/mod_devicetable.h>"""
new_inc = """#include <linux/array_size.h>
#include <linux/delay.h>
#include <linux/dev_printk.h>
#include <linux/err.h>
#include <linux/gpio.h>
#include <linux/mod_devicetable.h>"""
assert s.count(old_inc) == 1
s = s.replace(old_inc, new_inc, 1)

old_wr = """static const struct snd_soc_dapm_widget mt6765_mt6357_widgets[] = {
	SND_SOC_DAPM_OUTPUT("HDMI Out"),
};

static const struct snd_soc_dapm_route mt6765_mt6357_routes[] = {
	{"HDMI Out", NULL, "2ND I2S Playback"},
	{"DMIC In", NULL, "MICBIAS0"},
};"""
new_wr = """#define DANDELION_SPK_AMP_GPIO	665

static int spk_amp_gpio = -1;

static int mt6765_mt6357_spk_amp_event(struct snd_soc_dapm_widget *w,
				       struct snd_kcontrol *kcontrol, int event)
{
	int i;

	if (spk_amp_gpio < 0)
		return 0;

	switch (event) {
	case SND_SOC_DAPM_PRE_PMU:
		/* vendor Ext_Speaker_Amp_Change(): LOW -> 3x HIGH pulses */
		gpio_set_value(spk_amp_gpio, 0);
		usleep_range(1000, 2000);
		for (i = 0; i < 3; i++) {
			udelay(2);
			gpio_set_value(spk_amp_gpio, 1);
			udelay(2);
			gpio_set_value(spk_amp_gpio, 0);
		}
		udelay(2);
		gpio_set_value(spk_amp_gpio, 1);
		usleep_range(5000, 10000);
		break;
	case SND_SOC_DAPM_POST_PMD:
		gpio_set_value(spk_amp_gpio, 0);
		udelay(500);
		break;
	}

	return 0;
}

static const struct snd_soc_dapm_widget mt6765_mt6357_widgets[] = {
	SND_SOC_DAPM_OUTPUT("HDMI Out"),
	SND_SOC_DAPM_SUPPLY("Speaker Amp", SND_SOC_NOPM, 0, 0,
			    mt6765_mt6357_spk_amp_event,
			    SND_SOC_DAPM_PRE_PMU | SND_SOC_DAPM_POST_PMD),
};

static const struct snd_soc_dapm_route mt6765_mt6357_routes[] = {
	{"HDMI Out", NULL, "2ND I2S Playback"},
	{"DMIC In", NULL, "MICBIAS0"},
	{"Line out", NULL, "Speaker Amp"},
};"""
assert s.count(old_wr) == 1
s = s.replace(old_wr, new_wr, 1)

old_probe = """	struct mt6765_mt6357_priv *priv = snd_soc_card_get_drvdata(card);
	int ret, i;

	priv->pinctrl = devm_pinctrl_get(card->dev);"""
new_probe = """	struct mt6765_mt6357_priv *priv = snd_soc_card_get_drvdata(card);
	int ret, i;

	ret = devm_gpio_request_one(card->dev, DANDELION_SPK_AMP_GPIO,
				    GPIOF_OUT_INIT_LOW, "spk-amp-en");
	if (ret)
		dev_warn(card->dev, "speaker amp GPIO %d unavailable: %d\\n",
			 DANDELION_SPK_AMP_GPIO, ret);
	else
		spk_amp_gpio = DANDELION_SPK_AMP_GPIO;

	priv->pinctrl = devm_pinctrl_get(card->dev);"""
assert s.count(old_probe) == 1
s = s.replace(old_probe, new_probe, 1)

P.write_text(s, encoding="utf-8")
print("patched", P)
