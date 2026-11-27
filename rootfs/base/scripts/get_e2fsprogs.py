import os, subprocess, urllib.request, tarfile

D = os.path.expanduser("~/dandelion-ubuntu")
apk = os.path.join(D, "e2fsprogs-static.apk")
url = "https://dl-cdn.alpinelinux.org/alpine/v3.24/main/aarch64/e2fsprogs-static-1.47.4-r0.apk"
if not os.path.exists(apk):
    urllib.request.urlretrieve(url, apk)
print("apk size:", os.path.getsize(apk))

out = os.path.join(D, "e2fsprogs-static")
os.makedirs(out, exist_ok=True)
# apk is a gzip tar; signature block at the end does not prevent tarfile
with tarfile.open(apk) as t:
    t.extractall(out)
print("extracted")

for root, _d, files in os.walk(out):
    for f in files:
        p = os.path.join(root, f)
        if f in ("mke2fs", "mkfs.ext4", "resize2fs", "e2fsck") or f.startswith("lib"):
            print(os.path.relpath(p, out), os.path.getsize(p))
