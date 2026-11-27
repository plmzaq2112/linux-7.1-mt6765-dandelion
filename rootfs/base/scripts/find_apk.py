import re, urllib.request

url = "https://dl-cdn.alpinelinux.org/alpine/v3.24/main/aarch64/"
html = urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "replace")
names = sorted(set(re.findall(r'e2fsprogs[a-z-]*-[0-9][^"]*\.apk', html)))
for n in names:
    print(n)
