import re, shutil

V = "/home/a12bbb/dandelion-linux-kernel/01-pure-baseline/drivers/input/touchscreen/ft8006s_spi"
R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"

shutil.copy2(V + "/focaltech_core.c", R + "/focaltech_core.c")
p = R + "/focaltech_core.c"
s = open(p).read()

# include
s = s.replace("#include <linux/of_gpio.h>", "#include <linux/gpio/consumer.h>")

# FB event constants, inserted right before private header include
guard = '''/* 7.1 removed the fbdev blank notifier events */
#ifndef FB_EARLY_EVENT_BLANK
#define FB_EARLY_EVENT_BLANK 0x10
#endif
#ifndef FB_EVENT_BLANK
#define FB_EVENT_BLANK 0x09
#endif

'''
anchor = '#include "focaltech_core.h"'
s = s.replace(anchor, guard + anchor, 1)

# fields (avoid _flags by using word boundary before '_gpio')
s = s.replace("pdata->reset_gpio_flags", "__KEEP_RESET_FLAGS__")
s = s.replace("pdata->irq_gpio_flags", "__KEEP_IRQ_FLAGS__")
s = s.replace("pdata->reset_gpio", "pdata->reset_gpiod")
s = s.replace("pdata->irq_gpio", "pdata->irq_gpiod")
s = s.replace("__KEEP_RESET_FLAGS__", "pdata->reset_gpio_flags")
s = s.replace("__KEEP_IRQ_FLAGS__", "pdata->irq_gpio_flags")

# gpio api
s = s.replace("gpio_direction_output(", "gpiod_direction_output(")
s = s.replace("gpio_direction_input(", "gpiod_direction_input(")
s = s.replace("gpio_to_irq(", "gpiod_to_irq(")
s = re.sub(r'\bret = gpio_request\([^;]*\);', 'ret = 0;', s)
s = re.sub(r'\bgpio_free\([^;]*\);', '(void)0;', s)

# of_get_named_gpio_flags -> fwnode_gpiod_get_index
s = re.sub(
    r'pdata->reset_gpiod = of_get_named_gpio_flags\(np, "focaltech,reset-gpio",\s*\n\s*0, &pdata->reset_gpio_flags\);',
    'pdata->reset_gpiod = fwnode_gpiod_get_index(of_fwnode_handle(np), "focaltech,reset",\n'
    '                    0, GPIOD_ASIS, "fts_reset");',
    s, count=1)
s = re.sub(
    r'pdata->irq_gpiod = of_get_named_gpio_flags\(np, "focaltech,irq-gpio",\s*\n\s*0, &pdata->irq_gpio_flags\);',
    'pdata->irq_gpiod = fwnode_gpiod_get_index(of_fwnode_handle(np), "focaltech,irq",\n'
    '                    0, GPIOD_ASIS, "fts_irq");',
    s, count=1)
s = s.replace("if (pdata->reset_gpiod < 0)", "if (IS_ERR(pdata->reset_gpiod))")
s = s.replace("if (pdata->irq_gpiod < 0)", "if (IS_ERR(pdata->irq_gpiod))")

# gpio_is_valid
s = s.replace("if (gpio_is_valid(data->pdata->irq_gpiod))", "if (data->pdata->irq_gpiod)")
s = s.replace("if (gpio_is_valid(data->pdata->reset_gpiod))", "if (data->pdata->reset_gpiod)")
s = s.replace("if (gpio_is_valid(ts_data->pdata->reset_gpiod))", "if (ts_data->pdata->reset_gpiod)")
s = s.replace("if (gpio_is_valid(ts_data->pdata->irq_gpiod))", "if (ts_data->pdata->irq_gpiod)")
s = s.replace("if (gpio_is_valid(data->pdata->irq_gpiod))", "if (data->pdata->irq_gpiod)")
s = s.replace("if (gpio_is_valid(data->pdata->reset_gpiod))", "if (data->pdata->reset_gpiod)")

# remove: int -> void
s = s.replace("static int fts_ts_remove(struct spi_device *spi)",
              "static void fts_ts_remove(struct spi_device *spi)")
s = s.replace("    return fts_ts_remove_entry(spi_get_drvdata(spi));",
              "    fts_ts_remove_entry(spi_get_drvdata(spi));")

open(p, "w").write(s)

# verify leftovers
for pat in ("of_get_named_gpio", "gpio_is_valid", "pdata->reset_gpio\\b", "pdata->irq_gpio\\b"):
    print("leftover", pat, len(re.findall(pat, s)))
