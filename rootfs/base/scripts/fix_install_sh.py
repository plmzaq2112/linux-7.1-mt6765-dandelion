import os

for p in (os.path.expanduser("~/rootfs/ubuntu/scripts/install-p41.sh"),
          "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/scripts/install-p41.sh"):
    s = open(p).read()
    s = s.replace("usr/bin/phosh", "usr/libexec/phosh")
    open(p, "w").write(s)
    print("fixed", p)
