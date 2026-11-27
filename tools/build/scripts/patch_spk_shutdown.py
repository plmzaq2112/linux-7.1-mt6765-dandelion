#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/sound/soc/mediatek/mt6765/mt6765-mt6357.c")
s = P.read_text(encoding="utf-8")

# 1) widget: PRE_PMU only (amp off moved to PCM shutdown)
old = """	SND_SOC_DAPM_SUPPLY("Speaker Amp", SND_SOC_NOPM, 0, 0,
			    mt6765_mt6357_spk_amp_event,
			    SND_SOC_DAPM_PRE_PMU | SND_SOC_DAPM_POST_PMD),"""
new = """	SND_SOC_DAPM_SUPPLY("Speaker Amp", SND_SOC_NOPM, 0, 0,
			    mt6765_mt6357_spk_amp_event,
			    SND_SOC_DAPM_PRE_PMU),"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

# 2) drop POST_PMD case
old = """	case SND_SOC_DAPM_POST_PMD:
		gpio_set_value(spk_amp_gpio, 0);
		udelay(500);
		break;
	}"""
new = """	}"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

# 3) amp off at PCM shutdown, before DAPM powers down the codec
old = """	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		if (IS_ERR(priv->pin_states[PIN_STATE_MOSI_OFF]))
			return;"""
new = """	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		/* Mute the external amp before the codec LO powers down. */
		if (spk_amp_gpio >= 0) {
			gpio_set_value(spk_amp_gpio, 0);
			udelay(500);
		}

		if (IS_ERR(priv->pin_states[PIN_STATE_MOSI_OFF]))
			return;"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched shutdown handling")
