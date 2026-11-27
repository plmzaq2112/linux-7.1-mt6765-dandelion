import re

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"

# ---- core.c ----
p = R + "/focaltech_core.c"
s = open(p).read()
s = s.replace("irq_gpiod_flags", "irq_gpio_flags").replace("reset_gpiod_flags", "reset_gpio_flags")

# FB blank notifier: disable the callback body (no fbdev in this kernel)
s = s.replace("    case FB_EARLY_EVENT_BLANK:",
              "    case FB_EARLY_EVENT_BLANK: /* notifier kept, no fbdev */")
s = s.replace("    case FB_EVENT_BLANK:",
              "    case FB_EVENT_BLANK: /* notifier kept, no fbdev */")

# SPI driver .remove returns void in 7.1
s = s.replace("static int fts_ts_remove(struct spi_device *spi)",
              "static void fts_ts_remove(struct spi_device *spi)")
# add 'return;' before final closing brace of fts_ts_remove if it returns int literal
open(p, "w").write(s)
print("core.c fixed (flags/FB)")

# ---- ex_fun.c : define proc_ops ----
p = R + "/focaltech_ex_fun.c"
s = open(p).read()
if "static const struct proc_ops fts_proc_ops" not in s:
    # find the file_operations definition
    m = re.search(r'static const struct file_operations fts_proc_fops = \{(.*?)\};', s, re.S)
    if m:
        body = m.group(1)
        # map methods
        body = body.replace(".owner", ".owner")
        body = body.replace(".open", ".proc_open")
        body = body.replace(".read", ".proc_read")
        body = body.replace(".write", ".proc_write")
        body = body.replace(".release", ".proc_release")
        body = body.replace(".llseek", ".proc_lseek")
        newdef = "static const struct proc_ops fts_proc_ops = {" + body + "};\n"
        s = s[:m.start()] + newdef + s[m.end():]
        open(p, "w").write(s)
        print("ex_fun.c: proc_ops defined")
    else:
        print("ex_fun.c: fops pattern NOT found")
else:
    print("ex_fun.c: already")
