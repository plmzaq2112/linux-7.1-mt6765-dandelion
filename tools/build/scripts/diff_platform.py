import os, re

base = os.path.expanduser("~/dandelion-linux-kernel/01-pure-baseline/drivers/gpu/mediatek/gpu_rgx/m1.13ED5776728/services/system/rogue/rgx_mtk")

cands = []
for dp, _d, fs in os.walk(base):
    for fn in fs:
        if fn.endswith(".c"):
            cands.append(os.path.join(dp, fn))

print("files:", len(cands))
for p in cands:
    if "mtk_mfgsys" in p or "sysconfig" in p:
        print("\n=====", os.path.relpath(p, base))
        txt = open(p, errors="replace").read()
        # list function definitions and key register writes
        for i, line in enumerate(txt.split("\n"), 1):
            s = line.strip()
            if re.match(r"^(PVRSRV_ERROR|IMG_VOID|void|IMG_BOOL|static|int)\s+\w+\(.*\)\s*$", s) and not s.endswith(";"):
                print(f"{i}: {s[:110]}")
