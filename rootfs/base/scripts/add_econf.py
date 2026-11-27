import os, re, tarfile, urllib.request

D = os.path.expanduser("~/dandelion-ubuntu")
base = "https://dl-cdn.alpinelinux.org/alpine/v3.24/main/aarch64/"
html = urllib.request.urlopen(base, timeout=30).read().decode("utf-8", "replace")

names = sorted(set(re.findall(r'libeconf-[0-9][^"]*\.apk', html)))
print(names[:5])
stage = os.path.join(D, "e2fs-stage")
for n in names:
    apk = os.path.join(D, n)
    if not os.path.exists(apk):
        urllib.request.urlretrieve(base + n, apk)
    with tarfile.open(apk) as t:
        t.extractall(stage)
    print("extracted", n)

out = os.path.join(D, "e2fs-tools.tar.gz")
with tarfile.open(out, "w:gz") as t:
    for name in os.listdir(stage):
        t.add(os.path.join(stage, name), arcname=name)
print("packed", os.path.getsize(out))
