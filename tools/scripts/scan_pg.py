import re

p = "/home/a12bbb/dandelion-linux-kernel/01-pure-baseline/drivers/clk/mediatek/clk-mt6765-pg.c"
lines = open(p, errors="replace").read().split("\n")
print("total lines:", len(lines))

# find function definitions containing mfg
for i, l in enumerate(lines, 1):
    if re.search(r"^(static\s+)?(int|void|u32|unsigned)\s+\w*mfg\w*\s*\(", l):
        print(f"{i}: {l.strip()}")

print("\n--- TOPAXI protect hits ---")
for i, l in enumerate(lines, 1):
    if "TOPAXI" in l or "protect" in l.lower():
        print(f"{i}: {l.strip()[:120]}")
