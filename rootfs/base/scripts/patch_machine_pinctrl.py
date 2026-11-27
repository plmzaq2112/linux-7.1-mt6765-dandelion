import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/sound/soc/mediatek/mt6765/mt6765-mt6357.c")
s = open(p).read()

if "skipping pin states" in s:
    print("already patched")
    raise SystemExit

old = """	priv->pinctrl = devm_pinctrl_get(card->dev);
	if (IS_ERR(priv->pinctrl)) {
		ret = PTR_ERR(priv->pinctrl);
		return dev_err_probe(card->dev, ret,
				     "Failed to get pinctrl\\n");
	}

	for (i = PIN_STATE_DEFAULT ; i < PIN_STATE_MAX ; i++) {"""

new = """	priv->pinctrl = devm_pinctrl_get(card->dev);
	if (IS_ERR(priv->pinctrl)) {
		ret = PTR_ERR(priv->pinctrl);
		if (ret == -EPROBE_DEFER)
			return ret;
		dev_info(card->dev, "No pinctrl, skipping pin states\\n");
		priv->pinctrl = NULL;
		for (i = PIN_STATE_DEFAULT ; i < PIN_STATE_MAX ; i++)
			priv->pin_states[i] = ERR_PTR(-ENODEV);
		goto pinctrl_done;
	}

	for (i = PIN_STATE_DEFAULT ; i < PIN_STATE_MAX ; i++) {"""

assert old in s, "pinctrl block not found"
s = s.replace(old, new, 1)

old2 = """			}
		}
	}
	return 0;
}

static struct snd_soc_card mt6765_mt6357_soc_card = {"""
new2 = """			}
		}
	}

pinctrl_done:
	return 0;
}

static struct snd_soc_card mt6765_mt6357_soc_card = {"""

assert old2 in s, "post-loop anchor not found"
s = s.replace(old2, new2, 1)

open(p, "w").write(s)
print("patched pinctrl optional")
