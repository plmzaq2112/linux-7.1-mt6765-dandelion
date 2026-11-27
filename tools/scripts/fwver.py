import os, re, hashlib, binascii

fw = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/data/fw/rgx.sh"
data = open(fw, "rb").read()
print("size:", len(data))
print("md5 :", hashlib.md5(data).hexdigest())
print("head:", binascii.hexlify(data[:64]).decode())

# ascii strings
strings = re.findall(rb"[ -~]{6,}", data)
print("strings:", len(strings))

pats = [rb"1\.1[0-9]", rb"ED[0-9]{6,}", rb"RGX", rb"version", rb"VERSION", rb"Dandelion|dandelion", rb"6765", rb"6762"]
seen = {}
for s in strings:
    for p in pats:
        if re.search(p, s):
            t = s.decode("latin1")
            if t not in seen:
                seen[t] = 0
            seen[t] += 1

for t, n in sorted(seen.items(), key=lambda x: -x[1])[:40]:
    print(f"{n:3d}x  {t[:100]}")

# search whole kernel tree for other rgx.sh copies
root = "/home/a12bbb/dandelion-linux-kernel"
print("\nother rgx.sh in trees:")
for dp, _d, fs in os.walk(root):
    for fn in fs:
        if fn in ("rgx.sh",) or fn.startswith("rgx.sh."):
            p = os.path.join(dp, fn)
            try:
                print(p, os.path.getsize(p))
            except OSError:
                pass
