import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/power/supply/bq256xx_charger.c")
s = open(p).read()

if "bat_defaults" in s:
    print("already patched")
    raise SystemExit

old1 = "\tstruct power_supply_battery_info *bat_info;\n"
new1 = "\tstruct power_supply_battery_info *bat_info = NULL;\n\tstruct power_supply_battery_info bat_defaults = { };\n"
assert old1 in s
s = s.replace(old1, new1, 1)

old2 = """\t\tdev_warn(bq->dev, "battery info missing, default values will be applied\\n");

\t\tbat_info->constant_charge_current_max_ua ="""
new2 = """\t\tdev_warn(bq->dev, "battery info missing, default values will be applied\\n");

\t\tbat_info = &bat_defaults;
\t\tbat_info->constant_charge_current_max_ua ="""
assert old2 in s
s = s.replace(old2, new2, 1)

old3 = "\tpower_supply_put_battery_info(bq->charger, bat_info);\n"
new3 = "\tif (bat_info != &bat_defaults)\n\t\tpower_supply_put_battery_info(bq->charger, bat_info);\n"
assert old3 in s
s = s.replace(old3, new3, 1)

open(p, "w").write(s)
print("patched hw_init error path")
