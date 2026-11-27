import os
for p in (os.path.expanduser("~/rootfs/ubuntu/scripts/install-p41.sh"),
          "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/scripts/install-p41.sh"):
    s = open(p).read()
    s = s.replace('nc -l -p 3801 | tar -xzf - -C "$MNT"',
                  'nc -l -p 3801 < /dev/null | tar -xzf - -C "$MNT"')
    open(p, "w").write(s)
    print("patched", p, "devnull" if "/dev/null |" in s else "NOT PATCHED")
