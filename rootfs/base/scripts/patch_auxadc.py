import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/iio/adc/mt6359-auxadc.c")
s = open(p).read()

if "1 << chan->scan_type.realbits" in s:
    print("already patched")
    raise SystemExit

old = """	if (mask == IIO_CHAN_INFO_SCALE) {
		*val = desc->r_ratio.numerator * cinfo->vref_mV;

		if (desc->r_ratio.denominator > 1) {
			*val2 = desc->r_ratio.denominator;
			return IIO_VAL_FRACTIONAL;
		}

		return IIO_VAL_INT;
	}"""

new = """	if (mask == IIO_CHAN_INFO_SCALE) {
		/*
		 * scale (mV/LSB) = vref * numerator / (2^realbits * denominator)
		 */
		*val = desc->r_ratio.numerator * cinfo->vref_mV;
		*val2 = (1 << chan->scan_type.realbits) *
			desc->r_ratio.denominator;
		return IIO_VAL_FRACTIONAL;
	}"""

assert old in s, "scale block not found"
s = s.replace(old, new, 1)

# BATADC is a battery voltage channel, not a resistance
s = s.replace("MTK_PMIC_IIO_CHAN(MT6357, bat_adc, BATADC, 0, 15, IIO_RESISTANCE),",
              "MTK_PMIC_IIO_CHAN(MT6357, bat_adc, BATADC, 0, 15, IIO_VOLTAGE),", 1)

open(p, "w").write(s)
print("patched auxadc scale + BATADC type")
