import os, re, tarfile, urllib.request

D = os.path.expanduser("~/dandelion-ubuntu")
base = "https://dl-cdn.alpinelinux.org/alpine/v3.24/main/aarch64/"
html = urllib.request.urlopen(base, timeout=30).read().decode("utf-8", "replace")
names = sorted(set(re.findall(r'[a-z0-9_-]*com[_-]err[^"]*\.apk', html)))
print(names[:8])

stage = os.path.join(D, "e2fs-stage")
for n in names:
    apk = os.path.join(D, n)
    if not os.path.exists(apk):
        urllib.request.urlretrieve(base + n, apk)
    with tarfile.open(apk) as t:
        t.extractall(stage)
    print("extracted", n)

found = []
for ld in (os.path.join(stage, "lib"), os.path.join(stage, "usr/lib")):
    if os.path.isdir(ld):
        found += os.listdir(ld)
print("libcom_err present:", any(f.startswith("libcom_err.so") for f in found))

out = os.path.join(D, "e2fs-tools.tar.gz")
with tarfile.open(out, "w:gz") as t:
    for name in os.listdir(stage):
        t.add(os.path.join(stage, name), arcname=name)
print("packed", os.path.getsize(out))
