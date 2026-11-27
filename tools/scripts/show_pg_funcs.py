import re

base = "/home/a12bbb/dandelion-linux-kernel/01-pure-baseline/drivers/clk/mediatek/"
c = open(base + "clk-mt6765-pg.c", errors="replace").read().split("\n")
h = open(base + "clk-mt6765-pg.h", errors="replace").read().split("\n")

def show(lines, a, b, tag):
    print(f"\n===== {tag} {a}-{b}")
    for i in range(a - 1, min(b, len(lines))):
        print(f"{i+1}: {lines[i]}")

show(c, 1335, 1420, "mfg bus_prot + pwr")
show(c, 1703, 1760, "mfg_core0")
show(c, 1803, 1860, "mfg_async")

print("\n===== masks in clk-mt6765-pg.h")
for i, l in enumerate(h, 1):
    if re.search(r"MFG|PWR_ON|PWR_ACK|SRAM|BUS_PROT|MTCMOS", l):
        print(f"{i}: {l.strip()[:140]}")
