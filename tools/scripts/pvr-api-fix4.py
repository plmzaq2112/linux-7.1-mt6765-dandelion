import os, re

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

changed = {}

def patch(path, patterns):
    p = os.path.join(R, path)
    s = open(p).read()
    orig = s
    for pat, rep in patterns:
        s = re.sub(pat, rep, s)
    if s != orig:
        open(p, "w").write(s)
        changed[path] = changed.get(path, 0) + 1

# vm_flags / mmap_sem / timer API drift
pats = [
    (r'(\w+)->vm_flags \|= ([^;]+);', r'vm_flags_set(\1, \2);'),
    (r'(\w+)->vm_flags &= ~([^;]+);', r'vm_flags_clear(\1, \2);'),
    (r'down_write\(&(\w+)->mmap_sem\)', r'mmap_write_lock(\1)'),
    (r'down_read\(&(\w+)->mmap_sem\)', r'mmap_read_lock(\1)'),
    (r'up_write\(&(\w+)->mmap_sem\)', r'mmap_write_unlock(\1)'),
    (r'up_read\(&(\w+)->mmap_sem\)', r'mmap_read_unlock(\1)'),
    (r'\bfrom_timer\(', r'timer_container_of('),
    (r'\bdel_timer_sync\(', r'timer_delete_sync('),
]

for root, dirs, files in os.walk(R):
    if "/services" not in root and "/kernel" not in root:
        continue
    for f in files:
        if f.endswith(".c"):
            rel = os.path.relpath(os.path.join(root, f), R)
            patch(rel, pats)

print("patched files:", len(changed))
for k in sorted(changed)[:20]:
    print(" ", k)

# ion_support_generic in the build?
mp = os.path.join(R, "Makefile")
s = open(mp).read()
for line in s.split("\n"):
    if "ion" in line:
        print("MAKEFILE:", line.strip())
