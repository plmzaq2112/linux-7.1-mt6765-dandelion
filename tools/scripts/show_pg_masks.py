import os, re

base = "/home/a12bbb/dandelion-linux-kernel/01-pure-baseline"
c = open(base + "/drivers/clk/mediatek/clk-mt6765-pg.c", errors="replace").read().split("\n")

def show(a, b, tag):
    print(f"\n===== {tag}")
    for i in range(a - 1, min(b, len(c))):
        print(f"{i+1}: {c[i]}")

show(1416, 1480, "mfg_pwr on/off")
show(1756, 1802, "mfg_core0 on")

print("\n===== includes")
for i, l in enumerate(c[:60], 1):
    if "#include" in l:
        print(f"{i}: {l.strip()}")

print("\n===== find mask definitions")
names = ["MFG_PROT_STEP1_0_MASK", "MFG_PROT_STEP2_0_MASK", "MFG_SRAM_PDN", "MFG_SRAM_PDN_ACK", "MFG_CORE0_SRAM_PDN", "MFG_CORE0_PWR_STA_MASK", "PWR_ISO", "PWR_CLK_DIS", "PWR_RST_B", "PWR_ON_2ND"]
hits = {n: [] for n in names}
for dp, _d, fs in os.walk(base + "/drivers"):
    for fn in fs:
        if not fn.endswith((".h", ".c")):
            continue
        p = os.path.join(dp, fn)
        try:
            for i, line in enumerate(open(p, errors="replace"), 1):
                for n in names:
                    if re.search(r"#define\s+" + n + r"\b", line):
                        hits[n].append((os.path.relpath(p, base), i, line.strip()[:110]))
        except OSError:
            pass
for n in names:
    print("--", n)
    for f, i, l in hits[n][:3]:
        print(f"   {f}:{i}: {l}")
