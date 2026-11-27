import re

p = "/home/a12bbb/dandelion-linux-kernel/01-pure-baseline/drivers/clk/mediatek/clk-mt6765-pg.c"
c = open(p, errors="replace").read().split("\n")

print("== PWR_ON / masks 120-360")
for i in range(119, 360):
    if re.search(r"#define\s+(PWR_ON|MFG_PWR_STA_MASK|MFG_ASYNC_PWR_STA_MASK|MFG_PROT_STEP|MFG_CORE0_SRAM_PDN_ACK|MFG_SRAM)", c[i]):
        print(f"{i+1}: {c[i].strip()[:130]}")
        # print continuation lines for multi-line macros
        j = i
        while c[j].rstrip().endswith("\\") and j + 1 < len(c):
            j += 1
            print(f"{j+1}: {c[j].strip()[:130]}")

print("\n== call sites of spm_mtcmos_ctrl_mfg_*")
for i, l in enumerate(c, 1):
    if "spm_mtcmos_ctrl_mfg" in l and "static int" not in l:
        print(f"{i}: {l.strip()[:130]}")

print("\n== mtcmos on/off tables mentioning MFG")
for i, l in enumerate(c, 1):
    if re.search(r"mtcmos.*mfg|mfg.*mtcmos", l, re.I):
        print(f"{i}: {l.strip()[:130]}")
