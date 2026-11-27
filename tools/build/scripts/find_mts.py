import os, re

root = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk")

def find(pattern, exts=(".c", ".h"), limit=20, regex=False):
    rx = re.compile(pattern if regex else re.escape(pattern))
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(exts):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if rx.search(line):
                            out.append((os.path.relpath(p, root), i, line.rstrip()))
                            if len(out) >= limit:
                                return out
            except OSError:
                pass
    return out

for pat in ["MTS_SCHEDULE_DM_VAL", "#define REGX"]:
    pass

for label, pat in [
    ("MTS_SCHEDULE_DM_VAL", "MTS_SCHEDULE_DM_VAL"),
    ("RGX_CR_MTS_SCHEDULE define", r"#define\s+RGX_CR_MTS_SCHEDULE\s+"),
    ("RGX_CR_MTS_SCHEDULE_TASK_NON_COUNTED", r"#define\s+RGX_CR_MTS_SCHEDULE_TASK_NON_COUNTED"),
    ("RGX_CR_MTS_SCHEDULE_DM_GP", r"#define\s+RGX_CR_MTS_SCHEDULE_DM_GP"),
]:
    print("==", label)
    for f, i, l in find(pat, regex=True, limit=6):
        print(f"{f}:{i}: {l[:160]}")
