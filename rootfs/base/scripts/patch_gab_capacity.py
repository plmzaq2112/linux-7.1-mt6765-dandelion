import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/power/supply/generic-adc-battery.c")
s = open(p).read()

if "POWER_SUPPLY_PROP_CAPACITY" in s:
    print("already patched")
    raise SystemExit

# 1) struct: add battery info pointer
old = """	struct gpio_desc *charge_finished;
};"""
new = """	struct gpio_desc *charge_finished;
	struct power_supply_battery_info *battery_info;
};"""
assert old in s
s = s.replace(old, new, 1)

# 2) static props: add capacity
old = """static const enum power_supply_property gab_props[] = {
	POWER_SUPPLY_PROP_STATUS,
};"""
new = """static const enum power_supply_property gab_props[] = {
	POWER_SUPPLY_PROP_STATUS,
	POWER_SUPPLY_PROP_CAPACITY,
};"""
assert old in s
s = s.replace(old, new, 1)

# 3) get_property: capacity from voltage + OCV table
old = """	case POWER_SUPPLY_PROP_TEMP:
		return gab_read_channel(adc_bat, GAB_TEMP, &val->intval);
	default:
		return -EINVAL;"""
new = """	case POWER_SUPPLY_PROP_TEMP:
		return gab_read_channel(adc_bat, GAB_TEMP, &val->intval);
	case POWER_SUPPLY_PROP_CAPACITY: {
		const struct power_supply_battery_ocv_table *table;
		int voltage, table_len, ret;

		if (!adc_bat->battery_info)
			return -ENODATA;

		ret = gab_read_channel(adc_bat, GAB_VOLTAGE, &voltage);
		if (ret)
			return ret;

		table = power_supply_find_ocv2cap_table(adc_bat->battery_info,
							25, &table_len);
		if (!table)
			return -ENODATA;

		val->intval = power_supply_ocv2cap_simple(table, table_len,
							  voltage);
		return 0;
	}
	default:
		return -EINVAL;"""
assert old in s
s = s.replace(old, new, 1)

# 4) probe: fetch battery info after registering the supply
old = """	adc_bat->psy = devm_power_supply_register(&pdev->dev, psy_desc, &psy_cfg);
	if (IS_ERR(adc_bat->psy))
		return dev_err_probe(&pdev->dev, PTR_ERR(adc_bat->psy), "Failed to register power-supply device\\n");"""
new = """	adc_bat->psy = devm_power_supply_register(&pdev->dev, psy_desc, &psy_cfg);
	if (IS_ERR(adc_bat->psy))
		return dev_err_probe(&pdev->dev, PTR_ERR(adc_bat->psy), "Failed to register power-supply device\\n");

	if (power_supply_get_battery_info(adc_bat->psy, &adc_bat->battery_info))
		adc_bat->battery_info = NULL;"""
assert old in s
s = s.replace(old, new, 1)

open(p, "w").write(s)
print("patched capacity into generic-adc-battery")
