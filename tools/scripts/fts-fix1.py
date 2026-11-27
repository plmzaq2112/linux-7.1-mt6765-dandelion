R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"

# ---------- core.c : gpio_is_valid(int) -> pointer checks ----------
p = R + "/focaltech_core.c"
s = open(p).read()
s = s.replace("if (gpio_is_valid(data->pdata->irq_gpio)) {",
              "if (data->pdata->irq_gpiod) {")
s = s.replace("if (gpio_is_valid(data->pdata->reset_gpio)) {",
              "if (data->pdata->reset_gpiod) {")
s = s.replace("if (gpio_is_valid(data->pdata->reset_gpio))\n        (void)0;",
              "if (data->pdata->reset_gpiod)\n        (void)0;")
s = s.replace("if (gpio_is_valid(data->pdata->irq_gpio))\n        (void)0;",
              "if (data->pdata->irq_gpiod)\n        (void)0;")
open(p, "w").write(s)
print("core.c: gpio_is_valid replaced")

# ---------- core.c : leftover pdata->reset_gpio / irq_gpio ----------
s = open(p).read()
s = s.replace("pdata->reset_gpio", "desc_to_gpio(pdata->reset_gpiod)")
s = s.replace("pdata->irq_gpio", "desc_to_gpio(pdata->irq_gpiod)")
# but the two assignments we wrote use pdata->reset_gpiod already; guard against double
s = s.replace("desc_to_gpio(pdata->reset_gpiod) =", "pdata->reset_gpiod =")
s = s.replace("desc_to_gpio(pdata->irq_gpiod) =", "pdata->irq_gpiod =")
open(p, "w").write(s)
print("core.c: leftover gpio fields fixed")

# ---------- ex_fun.c : print gpio numbers ----------
p = R + "/focaltech_ex_fun.c"
s = open(p).read()
s = s.replace("pdata->reset_gpio, pdata->irq_gpio, ts_data->irq",
              "pdata->reset_gpiod ? desc_to_gpio(pdata->reset_gpiod) : -1,\n"
              "                      pdata->irq_gpiod ? desc_to_gpio(pdata->irq_gpiod) : -1, ts_data->irq")
s = s.replace('proc->proc_entry = proc_create(PROC_NAME, 0777, NULL, &fts_proc_fops);',
              'proc->proc_entry = proc_create(PROC_NAME, 0777, NULL, &fts_proc_ops);')
open(p, "w").write(s)
print("ex_fun.c: gpio print + proc_ops name")

# ---------- Makefile : drop flash (uses removed get_fs/set_fs) ----------
p = R + "/Makefile"
s = open(p).read()
s = s.replace("obj-$(CONFIG_TOUCHSCREEN_FTS)\t+=  focaltech_flash.o",
              "#obj-$(CONFIG_TOUCHSCREEN_FTS)\t+=  focaltech_flash.o")
open(p, "w").write(s)
print("Makefile: flash disabled")
