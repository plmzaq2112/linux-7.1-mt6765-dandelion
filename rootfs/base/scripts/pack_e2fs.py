import os, re, subprocess, tarfile, urllib.request

D = os.path.expanduser("~/dandelion-ubuntu")
base = "https://dl-cdn.alpinelinux.org/alpine/v3.24/main/aarch64/"
html = urllib.request.urlopen(base, timeout=30).read().decode("utf-8", "replace")

def find(prefix):
    names = sorted(set(re.findall(prefix + r'-[0-9][^"]*\.apk', html)))
    return names[-1] if names else None

stage = os.path.join(D, "e2fs-stage")
for prefix in ("e2fsprogs", "e2fsprogs-libs", "libblkid", "libuuid"):
    n = find(prefix)
    if not n:
        print("missing apk for", prefix)
        continue
    apk = os.path.join(D, n)
    if not os.path.exists(apk):
        urllib.request.urlretrieve(base + n, apk)
    with tarfile.open(apk) as t:
        t.extractall(stage)
    print("extracted", n)

# pack the stage into a small tarball for the device
out = os.path.join(D, "e2fs-tools.tar.gz")
with tarfile.open(out, "w:gz") as t:
    for name in os.listdir(stage):
        t.add(os.path.join(stage, name), arcname=name)
print("packed", out, os.path.getsize(out), "bytes")

# check all NEEDED libs are present in the stage
libdirs = [os.path.join(stage, "lib"), os.path.join(stage, "usr/lib")]
found = []
for ld in libdirs:
    if os.path.isdir(ld):
        found += os.listdir(ld)
needed = ["libext2fs.so.2", "libcom_err.so.2", "libblkid.so.1", "libuuid.so.1", "libe2p.so.2"]
for n in needed:
    ok = any(f.startswith(n) for f in found)
    print(("OK   " if ok else "MISS ") + n)
