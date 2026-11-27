import os

v = "/home/a12bbb/dandelion-linux-kernel/01-pure-baseline"
m = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline"

def ls(root, sub, limit=40):
    p = os.path.join(root, sub)
    print(f"\n== {sub} @ {os.path.basename(root)}")
    if not os.path.isdir(p):
        print("   [missing]")
        return
    for name in sorted(os.listdir(p))[:limit]:
        fp = os.path.join(p, name)
        print("  ", "d" if os.path.isdir(fp) else "f", name)

ls(v, "drivers/gpu/mediatek")
ls(v, "drivers/gpu/mediatek/gpu_rgx")
ls(m, "drivers/gpu/mediatek")

# does mainline support mt6765 in mfg pmdomain?
p = os.path.join(m, "drivers/pmdomain/mediatek/mtk-mfg-pmdomain.c")
if os.path.exists(p):
    print("\n== mtk-mfg-pmdomain.c compatibles")
    for i, line in enumerate(open(p, errors="replace"), 1):
        if "compatible" in line or "mt6765" in line or "mtk_mfg" in line:
            print(f"{i}: {line.rstrip()[:120]}")

# vendor pg file header
p = os.path.join(v, "drivers/clk/mediatek/clk-mt6765-pg.c")
if os.path.exists(p):
    print("\n== clk-mt6765-pg.c (first 60 lines)")
    for i, line in enumerate(open(p, errors="replace"), 1):
        if i > 60:
            break
        print(f"{i}: {line.rstrip()[:120]}")
