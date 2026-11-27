import os, re, tarfile, urllib.request

D = os.path.expanduser("~/dandelion-ubuntu")
base = "https://dl-cdn.alpinelinux.org/alpine/v3.24/main/aarch64/"
html = urllib.request.urlopen(base, timeout=30).read().decode("utf-8", "replace")

def find(prefix):
    names = sorted(set(re.findall(prefix + r'-[0-9][^"]*\.apk', html)))
    return names[-1] if names else None

pkgs = {}
for prefix in ("e2fsprogs", "e2fsprogs-libs", "util-linux-libs"):
    n = find(prefix)
    if n:
        pkgs[prefix] = n
print(pkgs)

stage = os.path.join(D, "e2fs-stage")
os.makedirs(stage, exist_ok=True)
for name in pkgs.values():
    apk = os.path.join(D, name)
    if not os.path.exists(apk):
        urllib.request.urlretrieve(base + name, apk)
    with tarfile.open(apk) as t:
        t.extractall(stage)
    print("extracted", name)

print("stage files:")
for root, _d, files in os.walk(stage):
    for f in files:
        if f.startswith(("mke2fs", "mkfs", "fsck")):
            print("  ", os.path.relpath(os.path.join(root, f), stage))
