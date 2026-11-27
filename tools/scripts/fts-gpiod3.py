import re

p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi/focaltech_core.c"
s = open(p).read()

# replace the two of_get_named_gpio_flags blocks
s = s.replace('''pdata->reset_gpiod = of_get_named_gpio_flags(np, "focaltech,reset-gpio",
                        0, &pdata->reset_gpiod_flags);
    if (pdata->reset_gpiod < 0)
        FTS_ERROR("Unable to get reset_gpio");''',
'''pdata->reset_gpiod = fwnode_gpiod_get_index(of_fwnode_handle(np), "focaltech,reset",
                        0, GPIOD_ASIS, "fts_reset");
    if (IS_ERR(pdata->reset_gpiod))
        FTS_ERROR("Unable to get reset_gpio");''')

s = s.replace('''pdata->irq_gpiod = of_get_named_gpio_flags(np, "focaltech,irq-gpio",
                      0, &pdata->irq_gpiod_flags);
    if (pdata->irq_gpiod < 0)
        FTS_ERROR("Unable to get irq_gpio");''',
'''pdata->irq_gpiod = fwnode_gpiod_get_index(of_fwnode_handle(np), "focaltech,irq",
                      0, GPIOD_ASIS, "fts_irq");
    if (IS_ERR(pdata->irq_gpiod))
        FTS_ERROR("Unable to get irq_gpio");''')

# gpio_is_valid -> pointer check
s = s.replace("if (gpio_is_valid(ts_data->pdata->reset_gpiod))", "if (ts_data->pdata->reset_gpiod)")
s = s.replace("if (gpio_is_valid(ts_data->pdata->irq_gpiod))", "if (ts_data->pdata->irq_gpiod)")

open(p, "w").write(s)

for pat in ("of_get_named_gpio", "gpio_is_valid"):
    print("leftover", pat, len(re.findall(pat, s)))
