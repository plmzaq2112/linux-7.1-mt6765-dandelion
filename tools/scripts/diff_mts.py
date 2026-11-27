import os, re

base = os.path.expanduser("~/dandelion-linux-kernel/01-pure-baseline/drivers/gpu/mediatek/gpu_rgx/m1.13ED5776728")
ours = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk")

def scan(root, pat, exts=(".c",), limit=40):
    rx = re.compile(pat)
    out = []
    for dp, _d, fs in os.walk(root):
        for fn in fs:
            if not fn.endswith(exts):
                continue
            p = os.path.join(dp, fn)
            try:
                for i, line in enumerate(open(p, errors="replace"), 1):
                    if rx.search(line):
                        out.append((os.path.relpath(p, root), i, line.strip()[:130]))
                        if len(out) >= limit:
                            return out
            except OSError:
                pass
    return out

for label, pat in [("MTS registers (vendor)", r"RGX_CR_MTS_"),
                   ("MTS registers (ours)", r"RGX_CR_MTS_")]:
    root = base if "vendor" in label else ours
    print("=" * 20, label)
    for f, i, l in scan(root, pat):
        print(f"{f}:{i}: {l}")
