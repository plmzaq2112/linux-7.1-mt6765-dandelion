import os, re, shutil

R = os.path.expanduser("~/ubuntu/rootfs")
log = open(os.path.join(R, "tmp/aptdl.log"), errors="replace").read()
arch = os.path.join(R, "var/cache/apt/archives")

names = []
for line in log.splitlines():
    m = re.match(r"Get:\d+ \S+ \S+ \S+ (\S+) (\S+) (\S+) \[", line)
    if m:
        names.append((m.group(1), m.group(2), m.group(3)))

print("packages:", len(names))
missing = []
out = os.path.join(R, "root/debs")
os.makedirs(out, exist_ok=True)

for name, ver, a in names:
    # apt stores ':' in version as %3a
    ver_file = ver.replace(":", "%3a")
    fn = "%s_%s_%s.deb" % (name, ver_file, a)
    p = os.path.join(arch, fn)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(out, fn))
    else:
        # fallback: glob by prefix name_
        cands = [f for f in os.listdir(arch) if f.startswith(name + "_") and f.endswith(".deb")]
        if cands:
            shutil.copy2(os.path.join(arch, cands[0]), os.path.join(out, cands[0]))
        else:
            missing.append(fn)

files = sorted(os.listdir(out))
print("copied:", len(files))
for f in files:
    print("  ", f)
if missing:
    print("MISSING:", missing)
