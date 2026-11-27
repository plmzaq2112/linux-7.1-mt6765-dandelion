import os, re

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

def edit(rel, fn):
    p = os.path.join(R, rel)
    s = open(p).read()
    n = fn(s)
    if n != s:
        open(p, "w").write(n)
        return True
    return False

cnt = 0

# 1. tracepoint __assign_str(a, b) -> __assign_str(a)
for root, _, files in os.walk(R):
    for f in files:
        if f.endswith((".h", ".c")):
            p = os.path.join(root, f)
            s = open(p).read()
            n = re.sub(r'__assign_str\((\w+),\s*[^;]+\);', r'__assign_str(\1);', s)
            if n != s:
                open(p, "w").write(n)
                cnt += 1
print("trace assign_str files:", cnt)

# 2. dma_fence_ops debug callbacks removed in 6.11
def guard_fence(s):
    s = re.sub(r'^(\s*)\.fence_value_str\s*=.*$', r'\1/* .fence_value_str removed in 6.11 */', s, flags=re.M)
    s = re.sub(r'^(\s*)\.timeline_value_str\s*=.*$', r'\1/* .timeline_value_str removed in 6.11 */', s, flags=re.M)
    return s

for rel in ["kernel/drivers/staging/imgtec/pvr_fence.c",
            "kernel/drivers/staging/imgtec/pvr_sw_fence.c",
            "kernel/drivers/staging/imgtec/pvr_sync_file.c",
            "kernel/drivers/staging/imgtec/pvr_counting_timeline.c"]:
    if os.path.exists(os.path.join(R, rel)):
        print(rel, edit(rel, guard_fence))

# 3. arm64 uaccess renames
print("osfunc_arm64", edit("services/server/env/linux/osfunc_arm64.c",
      lambda s: s.replace("uaccess_enable()", "uaccess_enable_privileged()")
                 .replace("uaccess_disable()", "uaccess_disable_privileged()")))

# 4. platform_driver.remove returns void (6.11)
print("platform_drv", edit("kernel/drivers/staging/imgtec/pvr_platform_drv.c",
      lambda s: s.replace("static int pvr_remove(struct platform_device *pDev)",
                          "static void pvr_remove(struct platform_device *pDev)")))
