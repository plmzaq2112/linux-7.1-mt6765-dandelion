R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"

# ---------- focaltech_core.h : pdata stores gpio descriptors ----------
p = R + "/focaltech_core.h"
s = open(p).read()

if "#include <linux/gpio/consumer.h>" not in s:
    s = s.replace("#include <linux/gpio.h>",
                  "#include <linux/gpio.h>\n#include <linux/gpio/consumer.h>", 1)

old_pdata = """struct fts_ts_platform_data {
    u32 irq_gpio;
    u32 irq_gpio_flags;
    u32 reset_gpio;
    u32 reset_gpio_flags;"""
new_pdata = """struct fts_ts_platform_data {
    struct gpio_desc *irq_gpiod;
    struct gpio_desc *reset_gpiod;
    u32 irq_gpio_flags;
    u32 reset_gpio_flags;"""
if "irq_gpiod" not in s:
    assert old_pdata in s, "pdata struct not found"
    s = s.replace(old_pdata, new_pdata, 1)
    open(p, "w").write(s)
    print("core.h: pdata -> gpiod")
else:
    print("core.h: already")

# ---------- focaltech_core.c ----------
p = R + "/focaltech_core.c"
s = open(p).read()

reps = [
    # reset direction
    ("gpio_direction_output(fts_data->pdata->reset_gpio, 0);",
     "gpiod_direction_output(fts_data->pdata->reset_gpiod, 0);"),
    ("gpio_direction_output(fts_data->pdata->reset_gpio, 1);",
     "gpiod_direction_output(fts_data->pdata->reset_gpiod, 1);"),
    ("gpio_direction_output(ts_data->pdata->reset_gpio, 0);",
     "gpiod_direction_output(ts_data->pdata->reset_gpiod, 0);"),
    ("gpio_direction_output(ts_data->pdata->reset_gpio, 1 );",
     "gpiod_direction_output(ts_data->pdata->reset_gpiod, 1 );"),
    # irq
    ("ts_data->irq = gpio_to_irq(pdata->irq_gpio);",
     "ts_data->irq = gpiod_to_irq(pdata->irq_gpiod);"),
    # request/input
    ('ret = gpio_request(data->pdata->irq_gpio, "fts_irq_gpio");',
     'ret = gpiod_direction_input(data->pdata->irq_gpiod);'),
    ("ret = gpio_direction_input(data->pdata->irq_gpio);",
     "ret = 0;"),
    ('ret = gpio_request(data->pdata->reset_gpio, "fts_reset_gpio");',
     "ret = 0;"),
    ("ret = gpio_direction_output(data->pdata->reset_gpio, 1);",
     "ret = gpiod_direction_output(data->pdata->reset_gpiod, 1);"),
    # frees
    ("gpio_free(data->pdata->reset_gpio);", "(void)0;"),
    ("gpio_free(data->pdata->irq_gpio);", "(void)0;"),
    ("gpio_free(ts_data->pdata->reset_gpio);", "(void)0;"),
    ("gpio_free(ts_data->pdata->irq_gpio);", "(void)0;"),
    # commented-out line can stay but fix the type reference
    ("//      gpio_direction_output(fts_data->pdata->reset_gpio, 0 );",
     "//      gpiod_direction_output(fts_data->pdata->reset_gpiod, 0 );"),
]

n = 0
for a, b in reps:
    if a in s:
        s = s.replace(a, b)
        n += 1

# of_get_named_gpio_flags -> fwnode_gpiod_get_index
old_reset = """    pdata->reset_gpio = of_get_named_gpio_flags(np, "focaltech,reset-gpio",
"""
if old_reset in s:
    # replace the two statements entirely
    import re
    s = re.sub(
        r'    pdata->reset_gpio = of_get_named_gpio_flags\(np, "focaltech,reset-gpio",\s*\n\s*0, \(enum of_gpio_flags \*\)&pdata->reset_gpio_flags\);',
        '    pdata->reset_gpiod = fwnode_gpiod_get_index(of_fwnode_handle(np), "focaltech,reset", 0, GPIOD_ASIS, "fts_reset");\n'
        '    if (IS_ERR(pdata->reset_gpiod)) return PTR_ERR(pdata->reset_gpiod);',
        s, count=1)
    s = re.sub(
        r'    pdata->irq_gpio = of_get_named_gpio_flags\(np, "focaltech,irq-gpio",\s*\n\s*0, \(enum of_gpio_flags \*\)&pdata->irq_gpio_flags\);',
        '    pdata->irq_gpiod = fwnode_gpiod_get_index(of_fwnode_handle(np), "focaltech,irq", 0, GPIOD_ASIS, "fts_irq");\n'
        '    if (IS_ERR(pdata->irq_gpiod)) return PTR_ERR(pdata->irq_gpiod);',
        s, count=1)
    print("core.c: of_get_named_gpio_flags replaced")

open(p, "w").write(s)
print("core.c: %d simple replacements" % n)
