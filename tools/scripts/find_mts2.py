import os, re

root = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk")

targets = [
    (r"RGX_CR_MTS_SCHEDULE_DM_CLRMSK", 6),
    (r"RGX_CR_MTS_SCHEDULE_DM_DM0", 4),
    (r"RGXFWIF_DM_GP\b", 8),
    (r"#define\s+RGX_CR_MTS_SCHEDULE_DM_MASKFULL", 4),
]
for pat, lim in targets:
    rx = re.compile(pat)
    print("==", pat)
    n = 0
    for dirpath, _d, files in os.walk(root):
        for fn in files:
            if not fn.endswith((".h", ".c")):
                continue
            p = os.path.join(dirpath, fn)
            try:
                for i, line in enumerate(open(p, errors="replace"), 1):
                    if rx.search(line):
                        print(f"{os.path.relpath(p, root)}:{i}: {line.rstrip()[:150]}")
                        n += 1
                        if n >= lim:
                            break
            except OSError:
                pass
            if n >= lim:
                break
        if n >= lim:
            break
