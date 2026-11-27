import os, re

root = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
pats = [r"InfoVersion", r"FW version", r"FW Version", r"fw version", r"ui32Version", r"FWIF_.*VERSION"]
for p in pats:
    rx = re.compile(p)
    hits = 0
    print("==", p)
    for dp, _d, fs in os.walk(root):
        for fn in fs:
            if not fn.endswith((".c", ".h")):
                continue
            fp = os.path.join(dp, fn)
            try:
                for i, line in enumerate(open(fp, errors="replace"), 1):
                    if rx.search(line):
                        print(f"{os.path.relpath(fp, root)}:{i}: {line.strip()[:120]}")
                        hits += 1
                        if hits >= 8:
                            break
            except OSError:
                pass
            if hits >= 8:
                break
        if hits >= 8:
            break
