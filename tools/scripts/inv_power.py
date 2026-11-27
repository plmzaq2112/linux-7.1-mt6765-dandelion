import os

def ls(root, sub, depth=1, limit=60):
    p = os.path.join(root, sub)
    if not os.path.isdir(p):
        print(f"[missing] {sub}")
        return
    print(f"[ok] {sub}")
    for name in sorted(os.listdir(p))[:limit]:
        fp = os.path.join(p, name)
        tag = "d" if os.path.isdir(fp) else "f"
        print(f"   {tag} {name}")

v = "/home/a12bbb/dandelion-linux-kernel/01-pure-baseline"      # 4.19 vendor
m = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline"       # 7.1 mainline

print("=== vendor 4.19: GPU 相关 ===")
ls(v, "drivers/misc/mediatek/gpu")
ls(v, "drivers/misc/mediatek/gpu/ged")
ls(v, "drivers/misc/mediatek/base/power")
ls(v, "drivers/misc/mediatek/base/power/mt6765")
ls(v, "drivers/clk/mediatek", limit=40)

print("\n=== mainline 7.1: 对应部分 ===")
ls(m, "drivers/pmdomain/mediatek")
ls(m, "drivers/clk/mediatek", limit=40)
ls(m, "drivers/misc/mediatek", limit=20)
ls(m, "drivers/gpu", limit=20)
