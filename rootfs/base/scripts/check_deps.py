import os, re, subprocess, urllib.request

base = "https://dl-cdn.alpinelinux.org/alpine/v3.24/main/aarch64/"
html = urllib.request.urlopen(base, timeout=30).read().decode("utf-8", "replace")
for pat in (r'[a-z0-9-]*blkid[^"]*\.apk', r'[a-z0-9-]*uuid[^"]*\.apk', r'util-linux[^"]*\.apk'):
    names = sorted(set(re.findall(pat, html)))
    print(pat, "->", names[:8])

D = os.path.expanduser("~/dandelion-ubuntu")
mke2fs = os.path.join(D, "e2fs-stage/sbin/mke2fs")
out = subprocess.run(["readelf", "-d", mke2fs], capture_output=True, text=True).stdout
print("\nNEEDED:")
for line in out.split("\n"):
    if "NEEDED" in line:
        print(" ", line.strip())
