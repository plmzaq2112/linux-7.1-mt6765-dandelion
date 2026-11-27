R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"

# ex_fun.c: remove owner (two spaces variant)
p = R + "/focaltech_ex_fun.c"
s = open(p).read()
s = s.replace("    .owner  = THIS_MODULE,\n", "")
s = s.replace("    .owner = THIS_MODULE,\n", "")
open(p, "w").write(s)
print("ex_fun: owner removed:", ".owner" not in s)

# core.c
p = R + "/focaltech_core.c"
s = open(p).read()

# comment the fb notifier function entirely
start = s.find("static int fts_fb_notifier_callback(")
if start >= 0:
    # find the closing brace at column 0 after start
    end = s.find("\n}\n", start)
    if end > 0:
        block = s[start:end+3]
        commented = "\n".join("// " + l for l in block.splitlines()) + "\n"
        s = s[:start] + commented + s[end+3:]
        print("core: fb notifier commented")

# fts_ts_remove
s = s.replace("    return fts_ts_remove_entry(spi_get_drvdata(spi));",
              "    fts_ts_remove_entry(spi_get_drvdata(spi));")

open(p, "w").write(s)
print("core: remove fixed")
