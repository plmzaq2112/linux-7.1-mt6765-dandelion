import re

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"

# ---- ex_fun.c: proc_ops has no owner ----
p = R + "/focaltech_ex_fun.c"
s = open(p).read()
s = s.replace("\t.owner = THIS_MODULE,\n", "")
s = s.replace("    .owner = THIS_MODULE,\n", "")
open(p, "w").write(s)
print("ex_fun.c: owner removed")

# ---- core.c ----
p = R + "/focaltech_core.c"
s = open(p).read()

# 1) FB blank notifier: comment out the whole callback to avoid FB_* constants
m = re.search(r'static int fts_fb_notifier_callback\(.*?\n\}\n', s, re.S)
if m:
    body = m.group(0)
    commented = "\n".join("// " + line for line in body.splitlines()) + "\n"
    s = s[:m.start()] + commented + s[m.end():]
    print("core.c: fb notifier commented")

# 2) fts_ts_remove: return value -> none
s = s.replace("static void fts_ts_remove(struct spi_device *spi)", "static void fts_ts_remove(struct spi_device *spi)")
# inside that function, replace 'return 0;' with 'return;'
m = re.search(r'(static void fts_ts_remove\(struct spi_device \*spi\)\n\{.*?\n\})\n', s, re.S)
if m:
    body = m.group(1).replace("return 0;", "return;")
    s = s[:m.start(1)] + body + s[m.end(1):]
    print("core.c: fts_ts_remove return fixed")

open(p, "w").write(s)
